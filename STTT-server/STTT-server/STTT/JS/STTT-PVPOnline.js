document.addEventListener('DOMContentLoaded', () => {
    let socket;
    let gameId;
    let playerSymbol;
    let isMyTurn = false;
    let gameActive = false;
    let nextBoard = null;
    let gameMode = null;
    
    const connectionStatus = document.getElementById('connection-status');
    const gameModeContainer = document.getElementById('game-mode-container');
    const createRoomContainer = document.getElementById('create-room-container');
    const joinRoomContainer = document.getElementById('join-room-container');
    const randomMatchContainer = document.getElementById('random-match-container');
    const roomInfoContainer = document.getElementById('room-info-container');
    const gameInterface = document.getElementById('game-interface');
    const playerNameInput = document.getElementById('player-name');
    const creatorNameInput = document.getElementById('creator-name');
    const joinerNameInput = document.getElementById('joiner-name');
    const roomIdInput = document.getElementById('room-id');
    const joinGameBtn = document.getElementById('join-game-btn');
    const createRoomBtn = document.getElementById('create-room-btn');
    const randomMatchBtn = document.getElementById('random-match-btn');
    const joinRoomBtn = document.getElementById('join-room-btn');
    const createRoomSubmitBtn = document.getElementById('create-room-submit-btn');
    const joinRoomSubmitBtn = document.getElementById('join-room-submit-btn');
    const waitingMessage = document.getElementById('waiting-message');
    const gameBoard = document.getElementById('game-board');
    const restartButton = document.getElementById('restart-button');
    const backToMenuButton = document.getElementById('back-to-menu');
    const player1Name = document.getElementById('player1-name');
    const player1Symbol = document.getElementById('player1-symbol');
    const player1Card = document.getElementById('player1-card');
    const player1Status = document.getElementById('player1-status');
    const player2Name = document.getElementById('player2-name');
    const player2Symbol = document.getElementById('player2-symbol');
    const player2Card = document.getElementById('player2-card');
    const player2Status = document.getElementById('player2-status');
    const currentPlayerEl = document.getElementById('current-player');
    const gameResultModal = document.getElementById('game-result-modal');
    const resultTitle = document.getElementById('result-title');
    const resultMessage = document.getElementById('result-message');
    const modalRestartBtn = document.getElementById('modal-restart-btn');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const roomLink = document.getElementById('room-link');
    const roomIdDisplay = document.getElementById('room-id-display');
    const copyLinkBtn = document.getElementById('copy-link-btn');
    
    const backFromCreateRoomBtn = document.getElementById('back-from-create-room');
    const backFromJoinRoomBtn = document.getElementById('back-from-join-room');
    const backFromRandomMatchBtn = document.getElementById('back-from-random-match');
    const backFromRoomInfoBtn = document.getElementById('back-from-room-info');
    const backFromWaitingBtn = document.getElementById('back-from-waiting');
    const backToHomeBtn = document.getElementById('back-to-home');
    
    function connectToServer() {
        //连接服务器
        const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
        const host = window.location.hostname;
        const port = window.location.port ? `:${window.location.port}` : '';
        const serverUrl = `${protocol}://${host}${port}`;
        
        socket = io(serverUrl);
        //连接成功事件
        socket.on('connect', () => {
            connectionStatus.textContent = '已连接到服务器';
            connectionStatus.style.backgroundColor = '#d4edda';
            connectionStatus.style.color = '#155724';
            gameModeContainer.style.display = 'block';
        });
        //连接失败事件
        socket.on('connect_error', (error) => {
            connectionStatus.textContent = '连接服务器失败，请刷新页面重试';
            connectionStatus.style.backgroundColor = '#f8d7da';
            connectionStatus.style.color = '#721c24';
            console.error('连接错误:', error);
        });
        
        socket.on('roomCreated', (data) => {
            gameId = data.roomId;
            playerSymbol = data.player.symbol;
            
            roomLink.value = data.roomLink;
            roomIdDisplay.textContent = data.roomId;
            
            gameModeContainer.style.display = 'none';
            createRoomContainer.style.display = 'none';
            roomInfoContainer.style.display = 'block';
        });
        
        socket.on('roomNotFound', (data) => {
            alert(data.message);
            joinRoomContainer.style.display = 'block';
        });
        
        socket.on('roomFull', (data) => {
            alert(data.message);
            joinRoomContainer.style.display = 'block';
        });
        
        socket.on('waitingForPlayer', (data) => {
            randomMatchContainer.style.display = 'none';
            waitingMessage.style.display = 'block';
        });
        
        socket.on('gameStart', (data) => {
            gameId = data.gameId;
            
            if (data.players[0].id === socket.id) {
                playerSymbol = data.players[0].symbol;
                isMyTurn = data.currentPlayer === 0;
            } else {
                playerSymbol = data.players[1].symbol;
                isMyTurn = data.currentPlayer === 1;
            }
            
            player1Name.textContent = data.players[0].name;
            player1Symbol.textContent = data.players[0].symbol;
            player1Symbol.className = `player-symbol ${data.players[0].symbol.toLowerCase()}`;
            player1Card.className = `player-card player-${data.players[0].symbol.toLowerCase()}`;
            player1Status.textContent = '准备就绪';
            
            player2Name.textContent = data.players[1].name;
            player2Symbol.textContent = data.players[1].symbol;
            player2Symbol.className = `player-symbol ${data.players[1].symbol.toLowerCase()}`;
            player2Card.className = `player-card player-${data.players[1].symbol.toLowerCase()}`;
            player2Status.textContent = '准备就绪';
            
            updateGameInfo(data.currentPlayer, data.nextBoard);
            createBoard(data.board, data.smallBoardWinners, data.nextBoard);
            
            gameModeContainer.style.display = 'none';
            createRoomContainer.style.display = 'none';
            joinRoomContainer.style.display = 'none';
            randomMatchContainer.style.display = 'none';
            roomInfoContainer.style.display = 'none';
            waitingMessage.style.display = 'none';
            gameInterface.style.display = 'flex';
            restartButton.style.display = 'inline-block';
            
            gameActive = true;
        });
        
        socket.on('gameUpdate', (data) => {
            updateBoard(data.board, data.smallBoardWinners, data.nextBoard);
            updateGameInfo(data.currentPlayer, data.nextBoard);
            
            isMyTurn = (data.currentPlayer === 0 && playerSymbol === 'X') || (data.currentPlayer === 1 && playerSymbol === 'O');
        });
        
        socket.on('gameOver', (data) => {
            gameActive = false;
            
            if (data.winnerId === socket.id) {
                resultTitle.textContent = '恭喜你赢了！';
                resultMessage.textContent = '你赢得了这场游戏！';
            } else {
                resultTitle.textContent = '游戏结束';
                resultMessage.textContent = '很遗憾，你输了这局游戏。';
            }
            
            gameResultModal.style.display = 'flex';
        });
        
        socket.on('gameDraw', (data) => {
            gameActive = false;
            
            resultTitle.textContent = '平局';
            resultMessage.textContent = '这局游戏以平局结束！';
            
            gameResultModal.style.display = 'flex';
        });
        
        socket.on('gameRestarted', (data) => {
            updateBoard(data.board, data.smallBoardWinners, data.nextBoard);
            updateGameInfo(data.currentPlayer, data.nextBoard);
            
            isMyTurn = (data.currentPlayer === 0 && playerSymbol === 'X') || (data.currentPlayer === 1 && playerSymbol === 'O');
            
            gameActive = true;
            gameResultModal.style.display = 'none';
        });
        
        socket.on('opponentDisconnected', (data) => {
            gameActive = false;
            alert(data.message);
            location.reload();
        });
    }
    
    function updateGameInfo(currentPlayer, nextBoard) {
        // 更新玩家卡片的高亮状态来显示当前玩家
        if (currentPlayer === 0) {
            player1Card.classList.add('active');
            player2Card.classList.remove('active');
            player1Status.textContent = '当前回合';
            player2Status.textContent = '等待中';
            currentPlayerEl.textContent = player1Name.textContent;
        } else {
            player1Card.classList.remove('active');
            player2Card.classList.add('active');
            player1Status.textContent = '等待中';
            player2Status.textContent = '当前回合';
            currentPlayerEl.textContent = player2Name.textContent;
        }
        
        if (isMyTurn) {
            currentPlayerEl.style.color = '#22c55e'; // 绿色表示当前是我的回合
        } else {
            currentPlayerEl.style.color = '#ef4444'; // 红色表示等待对手
        }
    }
    
    function createBoard(board, smallBoardWinners, nextBoard) {
        gameBoard.innerHTML = '';
        
        for (let i = 0; i < 9; i++) {
            const smallBoard = document.createElement('div');
            smallBoard.className = 'small-board';
            smallBoard.dataset.boardIndex = i;
            
            if (smallBoardWinners[i] === 'X') {
                smallBoard.classList.add('won-by-x');
            } else if (smallBoardWinners[i] === 'O') {
                smallBoard.classList.add('won-by-o');
            }
            
            if (nextBoard === null || nextBoard === i) {
                smallBoard.classList.add('active');
            }
            
            for (let j = 0; j < 9; j++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.boardIndex = i;
                cell.dataset.cellIndex = j;
                
                if (board[i][j]) {
                    cell.textContent = board[i][j];
                    cell.classList.add(board[i][j].toLowerCase());
                }
                
                cell.addEventListener('click', handleCellClick);
                smallBoard.appendChild(cell);
            }
            
            gameBoard.appendChild(smallBoard);
        }
    }
    
    function updateBoard(board, smallBoardWinners, nextBoard) {
        for (let i = 0; i < 9; i++) {
            const smallBoard = document.querySelector(`.small-board[data-board-index="${i}"]`);
            
            smallBoard.classList.remove('won-by-x', 'won-by-o', 'active');
            
            if (smallBoardWinners[i] === 'X') {
                smallBoard.classList.add('won-by-x');
            } else if (smallBoardWinners[i] === 'O') {
                smallBoard.classList.add('won-by-o');
            }
            
            for (let j = 0; j < 9; j++) {
                const cell = smallBoard.querySelector(`.cell[data-cell-index="${j}"]`);
                cell.textContent = board[i][j] || '';
                cell.className = 'cell';
                
                if (board[i][j]) {
                    cell.classList.add(board[i][j].toLowerCase());
                }
            }
        }
        
        document.querySelectorAll('.small-board').forEach(board => {
            const boardIndex = parseInt(board.dataset.boardIndex);
            if (nextBoard === null || nextBoard === boardIndex) {
                board.classList.add('active');
            }
        });
    }
    
    function handleCellClick(event) {
        if (!gameActive || !isMyTurn) return;
        
        const boardIndex = parseInt(event.target.dataset.boardIndex);
        const cellIndex = parseInt(event.target.dataset.cellIndex);
        
        socket.emit('makeMove', {
            gameId: gameId,
            boardIndex: boardIndex,
            cellIndex: cellIndex
        });
    }
    
    function checkRoomIdInUrl() {
        const pathParts = window.location.pathname.split('/');
        if (pathParts.length > 2 && pathParts[1] === 'join') {
            const roomId = pathParts[2];
            if (roomId) {
                gameMode = 'join';
                roomIdInput.value = roomId;
                
                const checkConnection = setInterval(() => {
                    if (socket && socket.connected) {
                        clearInterval(checkConnection);
                        joinRoomContainer.style.display = 'block';
                    }
                }, 100);
            }
        }
    }
    //创建房间
    createRoomBtn.addEventListener('click', () => {
        gameMode = 'create';
        gameModeContainer.style.display = 'none';
        createRoomContainer.style.display = 'block';
    });
    //随机匹配
    randomMatchBtn.addEventListener('click', () => {
        gameMode = 'random';
        gameModeContainer.style.display = 'none';
        randomMatchContainer.style.display = 'block';
    });
    //加入房间
    joinRoomBtn.addEventListener('click', () => {
        gameMode = 'join';
        gameModeContainer.style.display = 'none';
        joinRoomContainer.style.display = 'block';
    });
    //创建房间提交
    createRoomSubmitBtn.addEventListener('click', () => {
        const playerName = creatorNameInput.value.trim();
        if (playerName) {
            socket.emit('createRoom', {playerName});
        } else {
            alert('请输入玩家名称');
        }
    });
    //加入房间提交
    joinRoomSubmitBtn.addEventListener('click', () => {
        const roomId = roomIdInput.value.trim();
        const playerName = joinerNameInput.value.trim();
        
        if (roomId && playerName) {
            socket.emit('joinRoom', { roomId, playerName });
        } else {
            alert('请输入房间ID和玩家名称');
        }
    });
    // 加入游戏
    joinGameBtn.addEventListener('click', () => {
        const playerName = playerNameInput.value.trim();
        if (playerName) {
            socket.emit('joinGame', {playerName});
        } else {
            alert('请输入玩家名称');
        }
    });
    //复制房间链接
    copyLinkBtn.addEventListener('click', () => {
        roomLink.select();
        document.execCommand('copy');
        
        const originalText = copyLinkBtn.textContent;
        copyLinkBtn.textContent = '已复制!';
        copyLinkBtn.style.backgroundColor = '#28a745';
        
        setTimeout(() => {
            copyLinkBtn.textContent = originalText;
            copyLinkBtn.style.backgroundColor = '';
        }, 2000);
    });
    
    playerNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            joinGameBtn.click();
        }
    });
    
    creatorNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            createRoomSubmitBtn.click();
        }
    });
    
    joinerNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            joinRoomSubmitBtn.click();
        }
    });
    
    restartButton.addEventListener('click', () => {
        if (gameActive) {
            if (confirm('确定要重新开始游戏吗？')) {
                socket.emit('restartGame', { gameId: gameId });
            }
        }
    });
    
    backToMenuButton.addEventListener('click', () => {
        if (gameActive) {
            if (confirm('确定要退出游戏吗？')) {
                window.location.href = '/HTML/STTT-start.html';
            }
        } else {
            window.location.href = '/HTML/STTT-start.html';
        }
    });
    
    backToHomeBtn.addEventListener('click', () => {
        window.location.href = '/HTML/STTT-start.html';
    });
    
    backFromCreateRoomBtn.addEventListener('click', () => {
        createRoomContainer.style.display = 'none';
        gameModeContainer.style.display = 'block';
        creatorNameInput.value = '';
    });
    
    backFromJoinRoomBtn.addEventListener('click', () => {
        joinRoomContainer.style.display = 'none';
        gameModeContainer.style.display = 'block';
        roomIdInput.value = '';
        joinerNameInput.value = '';
    });
    
    backFromRandomMatchBtn.addEventListener('click', () => {
        randomMatchContainer.style.display = 'none';
        gameModeContainer.style.display = 'block';
        playerNameInput.value = '';
    });
    
    backFromRoomInfoBtn.addEventListener('click', () => {
        if (confirm('确定要退出房间吗？')) {
            roomInfoContainer.style.display = 'none';
            gameModeContainer.style.display = 'block';
            if (gameId) {
                socket.emit('leaveRoom', { gameId: gameId });
                gameId = null;
            }
        }
    });
    
    backFromWaitingBtn.addEventListener('click', () => {
        if (confirm('确定要取消匹配吗？')) {
            waitingMessage.style.display = 'none';
            gameModeContainer.style.display = 'block';
            if (gameId) {
                socket.emit('leaveGame', { gameId: gameId });
                gameId = null;
            }
        }
    });
    
    modalRestartBtn.addEventListener('click', () => {
        socket.emit('restartGame', { gameId: gameId });
    });
    
    modalCloseBtn.addEventListener('click', () => {
        gameResultModal.style.display = 'none';
    });
    
    connectToServer();
    checkRoomIdInUrl();
});