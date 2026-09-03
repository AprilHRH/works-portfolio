const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const cors = require('cors');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname)); // 使用当前目录作为静态文件目录

// 游戏房间管理
const games = new Map();
const waitingPlayers = [];

// 生成房间ID
function generateRoomId() {
    return Math.random().toString(36).substring(2, 6).toUpperCase();
}

// 路由
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'HTML', 'STTT-start.html'));
});

// 处理房间链接
app.get('/join/:roomId', (req, res) => {
    const roomId = req.params.roomId;
    if (games.has(roomId)) {
        res.sendFile(path.join(__dirname, 'HTML', 'STTT-PVPOnline.html'));
    } else {
        res.status(404).send('房间不存在或已过期');
    }
});

// Socket.IO 连接处理
io.on('connection', (socket) => {
    console.log('用户连接:', socket.id);

    // 创建房间
    socket.on('createRoom', (data) => {
        const roomId = generateRoomId();
        const player = {
            id: socket.id,
            name: data.playerName,
            symbol: 'X'
        };

        const game = {
            id: roomId,
            players: [player],
            currentPlayer: 0,
            board: Array(9).fill(null).map(() => Array(9).fill(null)),
            smallBoardWinners: Array(9).fill(null),
            nextBoard: null,
            gameActive: true,
            status: 'waiting'
        };

        games.set(roomId, game);

        socket.join(roomId);
        socket.gameId = roomId;

        function getServerBaseUrl(socket) {
        const req = socket.request;
        const protocol = req.headers['x-forwarded-proto'] || (req.connection.encrypted ? 'https' : 'http');
        const host = req.headers.host || 'localhost:1156';
        return `${protocol}://${host}`;
        }


        socket.emit('roomCreated', {
            roomId: roomId,
            player: player,
            roomLink: `${getServerBaseUrl(socket)}/join/${roomId}`
        });

        console.log('房间创建:', roomId);
    });

    // 加入房间
    socket.on('joinRoom', (data) => {
        const game = games.get(data.roomId);
        
        if (!game) {
            socket.emit('roomNotFound', { message: '房间不存在' });
            return;
        }

        if (game.players.length >= 2) {
            socket.emit('roomFull', { message: '房间已满' });
            return;
        }

        const player = {
            id: socket.id,
            name: data.playerName,
            symbol: 'O'
        };

        game.players.push(player);
        socket.join(data.roomId);
        socket.gameId = data.roomId;
        game.status = 'playing';

        // 通知所有玩家游戏开始
        io.to(data.roomId).emit('gameStart', {
            gameId: data.roomId,
            players: game.players,
            currentPlayer: game.currentPlayer,
            board: game.board,
            smallBoardWinners: game.smallBoardWinners,
            nextBoard: game.nextBoard
        });

        console.log('玩家加入房间:', data.roomId);
    });

    // 加入游戏队列（随机匹配）
    socket.on('joinGame', (data) => {
        const player = {
            id: socket.id,
            name: data.playerName || `玩家${socket.id.substr(0, 4)}`,
            symbol: waitingPlayers.length === 0 ? 'X' : 'O'
        };

        if (waitingPlayers.length === 0) {
            // 第一个玩家等待
            waitingPlayers.push(player);
            socket.emit('waitingForPlayer', { message: '等待其他玩家加入...' });
            console.log(`${player.name} 加入等待队列`);
        } else {
            // 第二个玩家加入，开始游戏
            const firstPlayer = waitingPlayers.shift();
            const roomId = generateRoomId();

            const game = {
                id: roomId,
                players: [firstPlayer, player],
                currentPlayer: 0,
                board: Array(9).fill(null).map(() => Array(9).fill(null)),
                smallBoardWinners: Array(9).fill(null),
                nextBoard: null,
                gameActive: true,
                status: 'playing'
            };

            games.set(roomId, game);

            // 将两个玩家都加入房间
            io.sockets.sockets.get(firstPlayer.id).join(roomId);
            io.sockets.sockets.get(firstPlayer.id).gameId = roomId;
            socket.join(roomId);
            socket.gameId = roomId;

            // 通知游戏开始
            io.to(roomId).emit('gameStart', {
                gameId: roomId,
                players: game.players,
                currentPlayer: game.currentPlayer,
                board: game.board,
                smallBoardWinners: game.smallBoardWinners,
                nextBoard: game.nextBoard
            });

            console.log(`游戏 ${roomId} 开始: ${firstPlayer.name} (${firstPlayer.symbol}) vs ${player.name} (${player.symbol})`);
        }
    });

    // 兼容旧的 randomMatch 事件
    socket.on('randomMatch', (data) => {
        socket.emit('joinGame', data);
    });

    // 处理移动
    socket.on('makeMove', (data) => {
        const game = games.get(socket.gameId);
        
        if (!game || !game.gameActive) return;

        const currentPlayerIndex = game.currentPlayer;
        if (game.players[currentPlayerIndex].id !== socket.id) return;

        // 检查移动是否有效
        if (game.board[data.boardIndex][data.cellIndex] || 
            game.smallBoardWinners[data.boardIndex] || 
            (game.nextBoard !== null && game.nextBoard !== data.boardIndex)) {
            return; // 无效移动
        }

        // 更新游戏状态
        const currentPlayerSymbol = game.players[currentPlayerIndex].symbol;
        game.board[data.boardIndex][data.cellIndex] = currentPlayerSymbol;
        
        // 检查小棋盘胜负
        const smallBoardWinner = checkSmallBoardWinner(game.board[data.boardIndex]);
        if (smallBoardWinner) {
            game.smallBoardWinners[data.boardIndex] = smallBoardWinner;
            
            // 检查游戏胜负
            const gameWinner = checkGameWinner(game.smallBoardWinners);
            if (gameWinner && gameWinner !== 'draw') {
                game.gameActive = false;
                const winnerPlayer = game.players.find(p => p.symbol === gameWinner);
                io.to(socket.gameId).emit('gameOver', {
                    winnerId: winnerPlayer.id,
                    winner: gameWinner,
                    board: game.board,
                    smallBoardWinners: game.smallBoardWinners
                });
                console.log(`游戏 ${socket.gameId} 结束，获胜者: ${gameWinner}`);
                return;
            } else if (gameWinner === 'draw') {
                game.gameActive = false;
                io.to(socket.gameId).emit('gameDraw', {
                    board: game.board,
                    smallBoardWinners: game.smallBoardWinners
                });
                console.log(`游戏 ${socket.gameId} 平局`);
                return;
            }
        }

        // 确定下一个棋盘
        game.nextBoard = data.cellIndex;
        
        // 如果下一个棋盘已经被赢下，则玩家可以在任意棋盘下
        if (game.smallBoardWinners[game.nextBoard]) {
            game.nextBoard = null;
        }
        
        // 切换玩家
        game.currentPlayer = (game.currentPlayer + 1) % 2;
        
        io.to(socket.gameId).emit('gameUpdate', {
            board: game.board,
            smallBoardWinners: game.smallBoardWinners,
            currentPlayer: game.currentPlayer,
            nextBoard: game.nextBoard,
            lastMove: {
                boardIndex: data.boardIndex,
                cellIndex: data.cellIndex,
                symbol: currentPlayerSymbol
            }
        });
    });

    // 重新开始游戏
    socket.on('restartGame', () => {
        const game = games.get(socket.gameId);
        
        if (game) {
            game.board = Array(9).fill(null).map(() => Array(9).fill(null));
            game.smallBoardWinners = Array(9).fill(null);
            game.nextBoard = null;
            game.currentPlayer = 0;
            game.gameActive = true;

            io.to(socket.gameId).emit('gameRestarted', {
                board: game.board,
                smallBoardWinners: game.smallBoardWinners,
                currentPlayer: game.currentPlayer,
                nextBoard: game.nextBoard
            });
        }
    });

    // 断开连接
    socket.on('disconnect', () => {
        console.log('用户断开连接:', socket.id);
        
        // 从等待列表中移除
        const index = waitingPlayers.findIndex(p => p.id === socket.id);
        if (index > -1) {
            waitingPlayers.splice(index, 1);
            return;
        }
        
        if (socket.gameId) {
            const game = games.get(socket.gameId);
            if (game) {
                // 通知其他玩家
                socket.to(socket.gameId).emit('opponentDisconnected', {
                    message: '对手已断开连接'
                });
                
                // 清理房间
                games.delete(socket.gameId);
            }
        }
    });
});

// 辅助函数
function checkSmallBoardWinner(board) {
    const lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], // 横线
        [0, 3, 6], [1, 4, 7], [2, 5, 8], // 竖线
        [0, 4, 8], [2, 4, 6] // 对角线
    ];

    for (let line of lines) {
        const [a, b, c] = line;
        if (board[a] && board[a] === board[b] && board[a] === board[c]) {
            return board[a];
        }
    }
    
    // 检查是否平局
    for (let i = 0; i < 9; i++) {
        if (!board[i]) {
            return null; // 还有空格，游戏继续
        }
    }
    
    return 'draw'; // 平局
}

function checkGameWinner(smallBoardWinners) {
    const lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], // 横线
        [0, 3, 6], [1, 4, 7], [2, 5, 8], // 竖线
        [0, 4, 8], [2, 4, 6] // 对角线
    ];

    for (let line of lines) {
        const [a, b, c] = line;
        if (smallBoardWinners[a] && smallBoardWinners[a] !== 'draw' && 
            smallBoardWinners[a] === smallBoardWinners[b] && 
            smallBoardWinners[a] === smallBoardWinners[c]) {
            return smallBoardWinners[a];
        }
    }
    
    // 检查是否平局
    for (let i = 0; i < 9; i++) {
        if (!smallBoardWinners[i]) {
            return null; // 还有小棋盘未结束，游戏继续
        }
    }
    
    return 'draw'; // 平局
}

const PORT = process.env.PORT || 1156;
server.listen(PORT, () => {
    console.log(`服务器运行在端口 ${PORT}`);
});