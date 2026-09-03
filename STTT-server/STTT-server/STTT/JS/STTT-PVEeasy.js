document.addEventListener('DOMContentLoaded', () => {
    let currentPlayer;
    let nextBoard = null;
    let gameActive = true;
    let playerSymbol;
    let aiSymbol;
    
    const smallBoards = Array(9).fill(null).map(() => Array(9).fill(''));
    const smallBoardWinners = Array(9).fill(null);
    let bigBoardWinner = null;
    const aiSearchDepth = 3;
    
    const gameBoard = document.getElementById('game-board');
    const aiThinkingStatus = document.getElementById('ai-thinking-status');
    const restartButton = document.getElementById('restart-button');
    const backToMenuButton = document.getElementById('back-to-menu');
    const selectDifficultyButton = document.getElementById('select-difficulty');
    
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
    const modalSelectDifficultyButton = document.getElementById('modal-select-difficulty');
    
    backToMenuButton.addEventListener('click', () => {
        window.location.href = '../HTML/STTT-start.html';
    });
    selectDifficultyButton.addEventListener('click', () => {
        window.location.href = '../HTML/STTT-start.html?show=ai-difficulty';
    });
    modalBackMenuButton.addEventListener('click', () => {
        window.location.href = '../HTML/STTT-start.html';
    });
    
    modalSelectDifficultyButton.addEventListener('click', () => {
        window.location.href = '../HTML/STTT-start.html?show=ai-difficulty';
    });
    
    modalRestartButton.addEventListener('click', () => {
        gameResultModal.classList.remove('show');
        initGame();
    });
    
    function initGame() {
        if (Math.random() < 0.85) {
            playerSymbol = 'X';
            aiSymbol = 'O';
            currentPlayer = 'X';
        } else {
            playerSymbol = 'O';
            aiSymbol = 'X';
            currentPlayer = 'X';
        }
        
        nextBoard = null;
        gameActive = true;
        bigBoardWinner = null;
        
        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {
                smallBoards[i][j] = '';
            }
            smallBoardWinners[i] = null;
        }
        
        if (playerSymbol === 'X') {
            playerXName.textContent = '玩家 X';
            playerOName.textContent = '电脑 O';
        } else {
            playerXName.textContent = '电脑 X';
            playerOName.textContent = '玩家 O';
        }
        
        aiThinkingStatus.textContent = '否';
        aiThinkingStatus.classList.remove('yes');
        aiThinkingStatus.classList.add('no');
        
        updatePlayerCards();
        createGameBoard();
        
        if (currentPlayer === aiSymbol) {
            aiThinkingStatus.textContent = '是';
            aiThinkingStatus.classList.remove('no');
            aiThinkingStatus.classList.add('yes');
            updatePlayerCards();
            setTimeout(makeAIMove, 1000);
        }
    }
    
    function updatePlayerCards() {
        playerXCard.classList.remove('active');
        playerOCard.classList.remove('active');
        playerXStatus.textContent = '等待中';
        playerOStatus.textContent = '等待中';
        
        if (currentPlayer === 'X') {
            playerXCard.classList.add('active');
            if (playerSymbol === 'X') {
                playerXStatus.textContent = '你的回合';
            } else {
                playerXStatus.textContent = '思考中...';
            }
        } else {
            playerOCard.classList.add('active');
            if (playerSymbol === 'O') {
                playerOStatus.textContent = '你的回合';
            } else {
                playerOStatus.textContent = '思考中...';
            }
        }
    }
    
    function createGameBoard() {
        gameBoard.innerHTML = '';
        
        for (let i = 0; i < 9; i++) {
            const smallBoard = document.createElement('div');
            smallBoard.classList.add('small-board');
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
                cell.classList.add('cell');
                cell.dataset.boardIndex = i;
                cell.dataset.cellIndex = j;
                
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
    
    function handleCellClick(e) {
        if (currentPlayer !== playerSymbol) return;
        
        const boardIndex = parseInt(e.target.dataset.boardIndex);
        const cellIndex = parseInt(e.target.dataset.cellIndex);
        
        if (!gameActive || smallBoards[boardIndex][cellIndex] || smallBoardWinners[boardIndex] || (nextBoard !== null && nextBoard !== boardIndex)) {
            return;
        }
        
        e.target.style.animation = 'pulse 0.3s ease-out';
        smallBoards[boardIndex][cellIndex] = currentPlayer;
        e.target.textContent = currentPlayer;
        e.target.classList.add(currentPlayer.toLowerCase());
        
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
        
        if (currentPlayer === aiSymbol && gameActive) {
            aiThinkingStatus.textContent = '是';
            aiThinkingStatus.classList.remove('no');
            aiThinkingStatus.classList.add('yes');
            updatePlayerCards();
            setTimeout(makeAIMove, 1000);
        }
    }
    
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
    
    function showGameResult(winner) {
        if (winner === 'draw') {
            resultTitle.textContent = '平局！';
            resultMessage.textContent = '双方势均力敌，不分胜负！';
        } else {
            const winnerName = winner === playerSymbol ? '玩家' : '电脑';
            resultTitle.textContent = '游戏结束！';
            resultMessage.textContent = `${winnerName} ${winner} 赢得了游戏！`;
        }
        
        playerXStatus.textContent = '游戏结束';
        playerOStatus.textContent = '游戏结束';
        playerXCard.classList.remove('active');
        playerOCard.classList.remove('active');
        
        gameResultModal.classList.add('show');
    }
    
    function makeAIMove() {
        if (!gameActive || currentPlayer !== aiSymbol) return;
        
        const startTime = performance.now();
        const availableMoves = [];
        
        for (let i = 0; i < 9; i++) {
            if (nextBoard !== null && i !== nextBoard) continue;
            if (smallBoardWinners[i]) continue;
            
            for (let j = 0; j < 9; j++) {
                if (!smallBoards[i][j]) {
                    availableMoves.push({ boardIndex: i, cellIndex: j });
                }
            }
        }
        
        if (availableMoves.length === 0) return;
        
        let selectedMove = null;
        
        selectedMove = findWinningMove(availableMoves, aiSymbol);
        if (selectedMove) {
            console.log("AI找到了获胜的移动");
        }
        
        if (!selectedMove) {
            selectedMove = findWinningMove(availableMoves, playerSymbol);
            if (selectedMove) {
                console.log("AI阻止了玩家的获胜");
            }
        }
        
        if (!selectedMove) {
            console.log("AI使用简化的Minimax算法选择最佳位置");
            
            let bestScore = -Infinity;
            let bestMove = null;
            const movesToConsider = availableMoves.slice(0, Math.min(availableMoves.length, 15));
            
            for (const move of movesToConsider) {
                smallBoards[move.boardIndex][move.cellIndex] = aiSymbol;
                
                const smallBoardWinner = checkSmallBoardWinner(move.boardIndex);
                const originalSmallBoardWinner = smallBoardWinners[move.boardIndex];
                
                if (smallBoardWinner === aiSymbol) {
                    smallBoardWinners[move.boardIndex] = aiSymbol;
                }
                
                const bigBoardWinner = checkBigBoardWinner();
                
                if (bigBoardWinner === aiSymbol) {
                    selectedMove = move;
                    smallBoards[move.boardIndex][move.cellIndex] = '';
                    smallBoardWinners[move.boardIndex] = originalSmallBoardWinner;
                    break;
                }
                
                const nextBoardAfterMove = smallBoardWinner ? null : move.cellIndex;
                
                const score = minimax(
                    aiSearchDepth - 1, 
                    false, 
                    -Infinity, 
                    Infinity, 
                    nextBoardAfterMove
                );
                
                smallBoards[move.boardIndex][move.cellIndex] = '';
                smallBoardWinners[move.boardIndex] = originalSmallBoardWinner;
                
                if (score > bestScore) {
                    bestScore = score;
                    bestMove = move;
                }
            }
            
            if (!selectedMove) {
                selectedMove = bestMove;
            }
        }
        
        if (!selectedMove) {
            selectedMove = findBestMove(availableMoves);
            console.log("AI使用进阶策略选择位置");
        }
        
        if (!selectedMove) {
            selectedMove = availableMoves[Math.floor(Math.random() * availableMoves.length)];
            console.log("AI随机选择位置");
        }
        
        if (selectedMove) {
            const { boardIndex, cellIndex } = selectedMove;
            
            smallBoards[boardIndex][cellIndex] = currentPlayer;
            
            const cellElement = document.querySelector(`.cell[data-board-index="${boardIndex}"][data-cell-index="${cellIndex}"]`);
            if (cellElement) {
                cellElement.textContent = currentPlayer;
                cellElement.classList.add(currentPlayer.toLowerCase());
                cellElement.style.animation = 'pulse 0.3s ease-out';
            }
            
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
                    createGameBoard();
                    showGameResult(bigBoardWinner);
                    return;
                }
            }
            
            nextBoard = cellIndex;
            
            if (smallBoardWinners[nextBoard]) {
                nextBoard = null;
            } 

            currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
            
            aiThinkingStatus.textContent = '否';
            aiThinkingStatus.classList.remove('yes');
            aiThinkingStatus.classList.add('no');
            
            const endTime = performance.now();
            console.log(`AI思考时间: ${(endTime - startTime).toFixed(2)} 毫秒`);
            
            updatePlayerCards();
            createGameBoard();
        }
    }
    
    function minimax(depth, isMaximizing, alpha, beta, currentNextBoard) {
        const bigBoardWinner = checkBigBoardWinner();
        
        if (depth === 0 || bigBoardWinner) {
            return evaluateBoard(bigBoardWinner);
        }
        
        const availableMoves = [];
        
        for (let i = 0; i < 9; i++) {
            if (currentNextBoard !== null && i !== currentNextBoard) continue;
            if (smallBoardWinners[i]) continue;
            
            for (let j = 0; j < 9; j++) {
                if (!smallBoards[i][j]) {
                    availableMoves.push({ boardIndex: i, cellIndex: j });
                }
            }
        }
        
        if (availableMoves.length === 0) {
            return evaluateBoard(null);
        }
        
        const movesToConsider = availableMoves.slice(0, Math.min(availableMoves.length, 10));
        
        if (isMaximizing) {
            let maxScore = -Infinity;
            
            for (const move of movesToConsider) {
                smallBoards[move.boardIndex][move.cellIndex] = aiSymbol;
                
                const smallBoardWinner = checkSmallBoardWinner(move.boardIndex);
                const originalSmallBoardWinner = smallBoardWinners[move.boardIndex];
                
                if (smallBoardWinner === aiSymbol) {
                    smallBoardWinners[move.boardIndex] = aiSymbol;
                }
                
                const nextBoardAfterMove = smallBoardWinner ? null : move.cellIndex;
                
                const score = minimax(depth - 1, false, alpha, beta, nextBoardAfterMove);
                
                smallBoards[move.boardIndex][move.cellIndex] = '';
                smallBoardWinners[move.boardIndex] = originalSmallBoardWinner;
                
                maxScore = Math.max(maxScore, score);
                alpha = Math.max(alpha, score);
                if (beta <= alpha) {
                    break;
                }
            }
            
            return maxScore;
        } else {
            let minScore = Infinity;
            
            for (const move of movesToConsider) {
                smallBoards[move.boardIndex][move.cellIndex] = playerSymbol;
                
                const smallBoardWinner = checkSmallBoardWinner(move.boardIndex);
                const originalSmallBoardWinner = smallBoardWinners[move.boardIndex];
                
                if (smallBoardWinner === playerSymbol) {
                    smallBoardWinners[move.boardIndex] = playerSymbol;
                }
                
                const nextBoardAfterMove = smallBoardWinner ? null : move.cellIndex;
                
                const score = minimax(depth - 1, true, alpha, beta, nextBoardAfterMove);
                
                smallBoards[move.boardIndex][move.cellIndex] = '';
                smallBoardWinners[move.boardIndex] = originalSmallBoardWinner;
                
                minScore = Math.min(minScore, score);
                beta = Math.min(beta, score);
                if (beta <= alpha) {
                    break;
                }
            }
            
            return minScore;
        }
    }
    
    function evaluateBoard(bigBoardWinner) {
        if (bigBoardWinner === aiSymbol) {
            return 1000;
        } else if (bigBoardWinner === playerSymbol) {
            return -1000;
        } else if (bigBoardWinner === 'draw') {
            return 0;
        }
        
        let score = 0;
        
        for (let i = 0; i < 9; i++) {
            if (smallBoardWinners[i] === aiSymbol) {
                score += 100;
                if (i === 4) {
                    score += 50;
                } else if ([0, 2, 6, 8].includes(i)) {
                    score += 25;
                }
            } else if (smallBoardWinners[i] === playerSymbol) {
                score -= 100;
                if (i === 4) {
                    score -= 50;
                } else if ([0, 2, 6, 8].includes(i)) {
                    score -= 25;
                }
            } else {
                score += evaluateSmallBoard(i);
            }
        }
        
        score += evaluateBigBoardPotential();
        
        return score;
    }
    
    function evaluateSmallBoard(boardIndex) {
        const board = smallBoards[boardIndex];
        let score = 0;
        
        const positionWeights = [
            3, 2, 3,
            2, 4, 2,
            3, 2, 3
        ];
        
        for (let i = 0; i < 9; i++) {
            if (board[i] === aiSymbol) {
                score += positionWeights[i];
            } else if (board[i] === playerSymbol) {
                score -= positionWeights[i];
            }
        }
        
        for (let i = 0; i < 3; i++) {
            const row = i * 3;
            let aiCount = 0;
            let playerCount = 0;
            
            for (let j = 0; j < 3; j++) {
                if (board[row + j] === aiSymbol) {
                    aiCount++;
                } else if (board[row + j] === playerSymbol) {
                    playerCount++;
                }
            }
            
            if (aiCount > 0 && playerCount === 0) {
                score += aiCount * aiCount * 10;
            } else if (playerCount > 0 && aiCount === 0) {
                score -= playerCount * playerCount * 10;
            }
        }
        
        for (let i = 0; i < 3; i++) {
            let aiCount = 0;
            let playerCount = 0;
            
            for (let j = 0; j < 3; j++) {
                if (board[i + j * 3] === aiSymbol) {
                    aiCount++;
                } else if (board[i + j * 3] === playerSymbol) {
                    playerCount++;
                }
            }
            
            if (aiCount > 0 && playerCount === 0) {
                score += aiCount * aiCount * 10;
            } else if (playerCount > 0 && aiCount === 0) {
                score -= playerCount * playerCount * 10;
            }
        }
        
        let aiCount = 0;
        let playerCount = 0;
        for (let i = 0; i < 3; i++) {
            if (board[i * 4] === aiSymbol) {
                aiCount++;
            } else if (board[i * 4] === playerSymbol) {
                playerCount++;
            }
        }
        if (aiCount > 0 && playerCount === 0) {
            score += aiCount * aiCount * 10;
        } else if (playerCount > 0 && aiCount === 0) {
            score -= playerCount * playerCount * 10;
        }
        
        aiCount = 0;
        playerCount = 0;
        for (let i = 0; i < 3; i++) {
            if (board[i * 2 + 2] === aiSymbol) {
                aiCount++;
            } else if (board[i * 2 + 2] === playerSymbol) {
                playerCount++;
            }
        }
        if (aiCount > 0 && playerCount === 0) {
            score += aiCount * aiCount * 10;
        } else if (playerCount > 0 && aiCount === 0) {
            score -= playerCount * playerCount * 10;
        }
        
        return score;
    }
    
    function evaluateBigBoardPotential() {
        let score = 0;
        
        for (let i = 0; i < 3; i++) {
            let aiCount = 0;
            let playerCount = 0;
            
            for (let j = 0; j < 3; j++) {
                const index = i * 3 + j;
                if (smallBoardWinners[index] === aiSymbol) {
                    aiCount++;
                } else if (smallBoardWinners[index] === playerSymbol) {
                    playerCount++;
                }
            }
            
            if (aiCount > 0 && playerCount === 0) {
                score += aiCount * aiCount * 50;
            } else if (playerCount > 0 && aiCount === 0) {
                score -= playerCount * playerCount * 50;
            }
        }
        
        for (let i = 0; i < 3; i++) {
            let aiCount = 0;
            let playerCount = 0;
            
            for (let j = 0; j < 3; j++) {
                const index = i + j * 3;
                if (smallBoardWinners[index] === aiSymbol) {
                    aiCount++;
                } else if (smallBoardWinners[index] === playerSymbol) {
                    playerCount++;
                }
            }
            
            if (aiCount > 0 && playerCount === 0) {
                score += aiCount * aiCount * 50;
            } else if (playerCount > 0 && aiCount === 0) {
                score -= playerCount * playerCount * 50;
            }
        }
        
        let aiCount = 0;
        let playerCount = 0;
        for (let i = 0; i < 3; i++) {
            const index = i * 4;
            if (smallBoardWinners[index] === aiSymbol) {
                aiCount++;
            } else if (smallBoardWinners[index] === playerSymbol) {
                playerCount++;
            }
        }
        if (aiCount > 0 && playerCount === 0) {
            score += aiCount * aiCount * 50;
        } else if (playerCount > 0 && aiCount === 0) {
            score -= playerCount * playerCount * 50;
        }
        
        aiCount = 0;
        playerCount = 0;
        for (let i = 0; i < 3; i++) {
            const index = i * 2 + 2;
            if (smallBoardWinners[index] === aiSymbol) {
                aiCount++;
            } else if (smallBoardWinners[index] === playerSymbol) {
                playerCount++;
            }
        }
        if (aiCount > 0 && playerCount === 0) {
            score += aiCount * aiCount * 50;
        } else if (playerCount > 0 && aiCount === 0) {
            score -= playerCount * playerCount * 50;
        }
        
        return score;
    }
    
    function findWinningMove(availableMoves, player) {
        for (const move of availableMoves) {
            const { boardIndex, cellIndex } = move;
            
            smallBoards[boardIndex][cellIndex] = player;
            
            const smallBoardWinner = checkSmallBoardWinner(boardIndex);
            
            smallBoards[boardIndex][cellIndex] = '';
            
            if (smallBoardWinner === player) {
                const originalWinner = smallBoardWinners[boardIndex];
                smallBoardWinners[boardIndex] = player;
                
                const bigBoardWinner = checkBigBoardWinner();
                
                smallBoardWinners[boardIndex] = originalWinner;
                
                if (bigBoardWinner === player) {
                    return move;
                }
            }
        }
        
        for (const move of availableMoves) {
            const { boardIndex, cellIndex } = move;
            
            smallBoards[boardIndex][cellIndex] = player;
            
            const smallBoardWinner = checkSmallBoardWinner(boardIndex);
            
            smallBoards[boardIndex][cellIndex] = '';
            
            if (smallBoardWinner === player) {
                return move;
            }
        }
        
        return null;
    }
    
    function findBestMove(availableMoves) {
        const positionWeights = [
            3, 2, 3,
            2, 4, 2,
            3, 2, 3
        ];
        
        let bestMove = null;
        let bestScore = -1;
        
        for (const move of availableMoves) {
            const { boardIndex, cellIndex } = move;
            let score = 0;
            
            score += positionWeights[cellIndex];
            score += evaluatePotentialWin(boardIndex, cellIndex, aiSymbol) * 2;
            score += evaluatePotentialWin(boardIndex, cellIndex, playerSymbol) * 1.5;
            score += evaluateBoardControl(boardIndex, cellIndex);
            score += evaluateNextBoardAdvantage(cellIndex);
            
            if (score > bestScore) {
                bestScore = score;
                bestMove = move;
            }
        }
        
        return bestMove;
    }
    
    function evaluatePotentialWin(boardIndex, cellIndex, player) {
        smallBoards[boardIndex][cellIndex] = player;
        
        let potentialWins = 0;
        const board = smallBoards[boardIndex];
        
        for (let i = 0; i < 3; i++) {
            const row = i * 3;
            let playerCount = 0;
            let emptyCount = 0;
            
            for (let j = 0; j < 3; j++) {
                if (board[row + j] === player) {
                    playerCount++;
                } else if (!board[row + j]) {
                    emptyCount++;
                }
            }
            
            if (playerCount > 0 && emptyCount > 0) {
                potentialWins += playerCount;
            }
        }
        
        for (let i = 0; i < 3; i++) {
            let playerCount = 0;
            let emptyCount = 0;
            
            for (let j = 0; j < 3; j++) {
                if (board[i + j * 3] === player) {
                    playerCount++;
                } else if (!board[i + j * 3]) {
                    emptyCount++;
                }
            }
            
            if (playerCount > 0 && emptyCount > 0) {
                potentialWins += playerCount;
            }
        }
        
        let playerCount = 0;
        let emptyCount = 0;
        for (let i = 0; i < 3; i++) {
            if (board[i * 4] === player) {
                playerCount++;
            } else if (!board[i * 4]) {
                emptyCount++;
            }
        }
        if (playerCount > 0 && emptyCount > 0) {
            potentialWins += playerCount;
        }
        
        playerCount = 0;
        emptyCount = 0;
        for (let i = 0; i < 3; i++) {
            if (board[i * 2 + 2] === player) {
                playerCount++;
            } else if (!board[i * 2 + 2]) {
                emptyCount++;
            }
        }
        if (playerCount > 0 && emptyCount > 0) {
            potentialWins += playerCount;
        }
        
        smallBoards[boardIndex][cellIndex] = '';
        
        return potentialWins;
    }
    
    function evaluateBoardControl(boardIndex, cellIndex) {
        let score = 0;
        const board = smallBoards[boardIndex];
        
        for (let i = 0; i < 9; i++) {
            if (board[i] === aiSymbol) {
                score += 1;
            }
        }
        
        if (boardIndex === 4) {
            score += 2;
        }
        
        if ([0, 2, 6, 8].includes(boardIndex)) {
            score += 1;
        }
        
        return score;
    }
    
    function evaluateNextBoardAdvantage(cellIndex) {
        if (smallBoardWinners[cellIndex] === aiSymbol) {
            return 3;
        }
        
        if (smallBoardWinners[cellIndex] === playerSymbol) {
            return -2;
        }
        
        if (cellIndex === 4) {
            return 1;
        }
        
        return 0;
    }
    
    function checkSmallBoardWinner(boardIndex) {
        const board = smallBoards[boardIndex];
        
        for (let i = 0; i < 3; i++) {
            if (board[i * 3] && board[i * 3] === board[i * 3 + 1] && board[i * 3] === board[i * 3 + 2]) {
                return board[i * 3];
            }
        }
        
        for (let i = 0; i < 3; i++) {
            if (board[i] && board[i] === board[i + 3] && board[i] === board[i + 6]) {
                return board[i];
            }
        }
        
        if (board[0] && board[0] === board[4] && board[0] === board[8]) {
            return board[0];
        }
        
        if (board[2] && board[2] === board[4] && board[2] === board[6]) {
            return board[2];
        }
        
        for (let i = 0; i < 9; i++) {
            if (!board[i]) {
                return null;
            }
        }
        
        return 'draw';
    }
    
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