document.addEventListener('DOMContentLoaded', () => {
    let currentPlayer;
    let nextBoard = null;
    let gameActive = true;
    
    const smallBoards = Array(9).fill(null).map(() => Array(9).fill(''));
    const smallBoardWinners = Array(9).fill(null);
    let bigBoardWinner = null;
    
    const gameBoard = document.getElementById('game-board');
    const restartButton = document.getElementById('restart-button');
    const backToMenuButton = document.getElementById('back-to-menu');
    
    const playerXCard = document.querySelector('.player-card.player-x');
    const playerOCard = document.querySelector('.player-card.player-o');
    const playerXStatus = playerXCard.querySelector('.player-status');
    const playerOStatus = playerOCard.querySelector('.player-status');
    const playerXName = playerXCard.querySelector('.player-name');
    const playerOName = playerOCard.querySelector('.player-name');
    
    const gameResultModal = document.getElementById('game-result-modal');
    const resultTitle = document.getElementById('result-title');
    const resultMessage = document.getElementById('result-message');
    const modalRestartButton = document.getElementById('modal-restart');
    const modalBackMenuButton = document.getElementById('modal-back-menu');
    
    backToMenuButton.addEventListener('click', () => {
        window.location.href = '../HTML/STTT-start.html';
    });
    
    modalBackMenuButton.addEventListener('click', () => {
        window.location.href = '../HTML/STTT-start.html';
    });
    
    modalRestartButton.addEventListener('click', () => {
        gameResultModal.classList.remove('show');
        initGame();
    });
    //初始化游戏
    function initGame() {
        currentPlayer = Math.random() < 0.5 ? 'X' : 'O';
        nextBoard = null;
        gameActive = true;
        bigBoardWinner = null;
        
        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {
                smallBoards[i][j] = '';
            }
            smallBoardWinners[i] = null;
        }
        
        playerXName.textContent = '玩家 1';
        playerOName.textContent = '玩家 2';
        
        updatePlayerCards();
        createGameBoard();
    }
    //更新玩家状态
    function updatePlayerCards() {
        playerXCard.classList.remove('active');
        playerOCard.classList.remove('active');
        playerXStatus.textContent = '等待中';
        playerOStatus.textContent = '等待中';
        
        if (currentPlayer === 'X') {
            playerXCard.classList.add('active');
            playerXStatus.textContent = '你的回合';
        } else {
            playerOCard.classList.add('active');
            playerOStatus.textContent = '你的回合';
        }
    }
    //创建棋盘
    function createGameBoard() {
        gameBoard.innerHTML = '';
        
        for (let i = 0; i < 9; i++) {
            const smallBoard = document.createElement('div');
            smallBoard.classList.add('small-board');
            smallBoard.dataset.boardIndex = i;
            //添加小棋盘的胜者
            if (smallBoardWinners[i] === 'X') {
                smallBoard.classList.add('won-by-x');
            } else if (smallBoardWinners[i] === 'O') {
                smallBoard.classList.add('won-by-o');
            }
            //高亮当前可下的小棋盘
            if (nextBoard === null || nextBoard === i) {
                smallBoard.classList.add('active');
            }
            //创建小棋盘的格子
            for (let j = 0; j < 9; j++) {
                const cell = document.createElement('div');
                cell.classList.add('cell');
                cell.dataset.boardIndex = i;
                cell.dataset.cellIndex = j;
                //填充已下的棋子
                if (smallBoards[i][j]) {
                    cell.textContent = smallBoards[i][j];
                    cell.classList.add(smallBoards[i][j].toLowerCase());
                }
                
                cell.addEventListener('click', handleCellClick);
                smallBoard.appendChild(cell);
            }
            
            gameBoard.appendChild(smallBoard);
        }
    }
    //处理格子点击
    function handleCellClick(e) {
        const boardIndex = parseInt(e.target.dataset.boardIndex);
        const cellIndex = parseInt(e.target.dataset.cellIndex);
        //验证是否可以下子
        if (!gameActive || smallBoards[boardIndex][cellIndex] || smallBoardWinners[boardIndex] || (nextBoard !== null && nextBoard !== boardIndex)) {
            return;
        }
        //纯粹的点击动画效果
        e.target.style.animation = 'pulse 0.3s ease-out';
        smallBoards[boardIndex][cellIndex] = currentPlayer;
        e.target.textContent = currentPlayer;
        e.target.classList.add(currentPlayer.toLowerCase());
        //检查小棋盘和大棋盘的胜利情况
        const smallBoardWinner = checkSmallBoardWinner(boardIndex);
        if (smallBoardWinner) {
            smallBoardWinners[boardIndex] = smallBoardWinner;
            
            const smallBoardElement = document.querySelector(`.small-board[data-board-index="${boardIndex}"]`);
            if (smallBoardWinner === 'X') {
                smallBoardElement.classList.add('won-by-x');
            } else {
                smallBoardElement.classList.add('won-by-o');
            }
            
            addWinningLine(boardIndex, smallBoardWinner);
            
            bigBoardWinner = checkBigBoardWinner();
            if (bigBoardWinner) {
                gameActive = false;
                playerXStatus.textContent = '游戏结束';
                playerOStatus.textContent = '游戏结束';
                showGameResult(bigBoardWinner);
                return;
            }
        }
        
        nextBoard = cellIndex;
        
        if (smallBoardWinners[nextBoard]) {
            nextBoard = null;
        } 
        
        currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
        
        updatePlayerCards();
        createGameBoard();
    }
    //划线
    function addWinningLine(boardIndex, winner) {
        const board = smallBoards[boardIndex];
        const smallBoardElement = document.querySelector(`.small-board[data-board-index="${boardIndex}"]`);
        
        for (let i = 0; i < 3; i++) {
            if (board[i * 3] && board[i * 3] === board[i * 3 + 1] && board[i * 3] === board[i * 3 + 2]) {
                smallBoardElement.classList.add(`row-${i}`);
                return;
            }
        }
        
        for (let i = 0; i < 3; i++) {
            if (board[i] && board[i] === board[i + 3] && board[i] === board[i + 6]) {
                smallBoardElement.classList.add(`col-${i}`);
                return;
            }
        }
        
        if (board[0] && board[0] === board[4] && board[0] === board[8]) {
            smallBoardElement.classList.add('diag-1');
            return;
        }
        
        if (board[2] && board[2] === board[4] && board[2] === board[6]) {
            smallBoardElement.classList.add('diag-2');
            return;
        }
    }
    //结果弹窗
    function showGameResult(winner) {
        if (winner === 'draw') {
            resultTitle.textContent = '平局！';
            resultMessage.textContent = '双方势均力敌，不分胜负！';
        } else {
            resultTitle.textContent = '游戏结束！';
            resultMessage.textContent = `玩家 ${winner === 'X' ? '1' : '2'} 赢得了游戏！`;
        }
        
        gameResultModal.classList.add('show');
    }
    //检查小棋盘胜者
    function checkSmallBoardWinner(boardIndex) {
        const board = smallBoards[boardIndex];
        //行检查
        for (let i = 0; i < 3; i++) {
            if (board[i * 3] && board[i * 3] === board[i * 3 + 1] && board[i * 3] === board[i * 3 + 2]) {
                return board[i * 3];
            }
        }
        //列检查
        for (let i = 0; i < 3; i++) {
            if (board[i] && board[i] === board[i + 3] && board[i] === board[i + 6]) {
                return board[i];
            }
        }
        //斜线检查
        if (board[0] && board[0] === board[4] && board[0] === board[8]) {
            return board[0];
        }
        
        if (board[2] && board[2] === board[4] && board[2] === board[6]) {
            return board[2];
        }
        //平局检查
        for (let i = 0; i < 9; i++) {
            if (!board[i]) {
                return null;
            }
        }
        
        return 'draw';
    }
    //检查大棋盘胜者一个道理，
    function checkBigBoardWinner() {
        for (let i = 0; i < 3; i++) {
            if (smallBoardWinners[i * 3] && smallBoardWinners[i * 3] !== 'draw' && 
                smallBoardWinners[i * 3] === smallBoardWinners[i * 3 + 1] && 
                smallBoardWinners[i * 3] === smallBoardWinners[i * 3 + 2]) {
                return smallBoardWinners[i * 3];
            }
        }
        
        for (let i = 0; i < 3; i++) {
            if (smallBoardWinners[i] && smallBoardWinners[i] !== 'draw' && 
                smallBoardWinners[i] === smallBoardWinners[i + 3] && 
                smallBoardWinners[i] === smallBoardWinners[i + 6]) {
                return smallBoardWinners[i];
            }
        }
        
        if (smallBoardWinners[0] && smallBoardWinners[0] !== 'draw' && 
            smallBoardWinners[0] === smallBoardWinners[4] && 
            smallBoardWinners[0] === smallBoardWinners[8]) {
            return smallBoardWinners[0];
        }
        
        if (smallBoardWinners[2] && smallBoardWinners[2] !== 'draw' && 
            smallBoardWinners[2] === smallBoardWinners[4] && 
            smallBoardWinners[2] === smallBoardWinners[6]) {
            return smallBoardWinners[2];
        }
        
        for (let i = 0; i < 9; i++) {
            if (!smallBoardWinners[i]) {
                return null;
            }
        }
        
        return 'draw';
    }
    
    restartButton.addEventListener('click', initGame);
    initGame();
});