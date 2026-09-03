document.addEventListener('DOMContentLoaded', () => {
    // 游戏状态变量
    let currentPlayer; //当前玩家回合
    let nextBoard = null;  //下一个必须下的小棋盘索引，null表示任意小棋盘
    let gameActive = true; //游戏是否进行中的标记
    let playerSymbol; //玩家符号
    let aiSymbol; //AI符号
    
    // 游戏数据结构
    const smallBoards = Array(9).fill(null).map(() => Array(9).fill(''));//大棋盘，有9个小棋盘，通过二维数组实现
    const smallBoardWinners = Array(9).fill(null); //记录每个小棋盘的获胜者
    let bigBoardWinner = null; //大棋盘的获胜者，null表示未获胜
    const aiSearchDepth = 10; //AI搜索深度，用于 minimax 判定
    
    // 获取页面元素
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
    
    // 页面导航事件监听
    backToMenuButton.addEventListener('click', () => {
        window.location.href = '../HTML/STTT-start.html';  //返回主菜单事件
    });
    
    selectDifficultyButton.addEventListener('click', () => {
        window.location.href = '../HTML/STTT-start.html?show=ai-difficulty';  //选择难度事件
    });
    
    modalSelectDifficultyButton.addEventListener('click', () => {
        window.location.href = '../HTML/STTT-start.html?show=ai-difficulty';  //重选难度事件
    });
    
    modalRestartButton.addEventListener('click', () => { //重新开始游戏事件
        gameResultModal.classList.remove('show');
        initGame();
    });
    
    // 初始化游戏
    function initGame() {
        //先后手，85%概率先手，电脑开头会很慢
        if (Math.random() < 0.85) {
            playerSymbol = 'X';
            aiSymbol = 'O';
            currentPlayer = 'X';
        } else {
            playerSymbol = 'O';
            aiSymbol = 'X';
            currentPlayer = 'X';
        }
        //init
        nextBoard = null;   //初始化，可以下任何小棋盘
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
        
        aiThinkingStatus.textContent = '否';    //AI初始状态为不思考
        aiThinkingStatus.classList.remove('yes');
        aiThinkingStatus.classList.add('no');
        
        updatePlayerCards();
        createGameBoard();
        
        if (currentPlayer === aiSymbol) {  //假如AI先手了
            aiThinkingStatus.textContent = '是';
            aiThinkingStatus.classList.remove('no');
            aiThinkingStatus.classList.add('yes');
            updatePlayerCards();
        }
    }
    
    // 更新玩家状态显示，轮到X或O
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
    
    // 创建游戏棋盘
    function createGameBoard() {
        gameBoard.innerHTML = ''; //清空游戏棋盘
    
        for (let i = 0; i < 9; i++) {     //创建9个小棋盘
            const smallBoard = document.createElement('div');
            smallBoard.classList.add('small-board');
            smallBoard.dataset.boardIndex = i;
        
            // 标记已获胜的小棋盘
            if (smallBoardWinners[i] === 'X') {
                smallBoard.classList.add('won-by-x');
            } else if (smallBoardWinners[i] === 'O') {
                smallBoard.classList.add('won-by-o');
            }
        
            // 标记当前可下的小棋盘
            if (nextBoard === null || nextBoard === i) {
                smallBoard.classList.add('active');
            }
        
            // 创建小棋盘中的9个格子
            for (let j = 0; j < 9; j++) {
                const cell = document.createElement('div');
                cell.classList.add('cell');
                cell.dataset.boardIndex = i;
                cell.dataset.cellIndex = j;
            
                // 显示已有棋子
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
    
    // 处理格子点击事件
    function handleCellClick(e) {
        if (currentPlayer !== playerSymbol) return;//不是自己的回合，忽略点击
    
        const boardIndex = parseInt(e.target.dataset.boardIndex); //获取点击的小棋盘索引
        const cellIndex = parseInt(e.target.dataset.cellIndex); //获取点击的格子索引
    
        // 检查移动是否合法
        if (!gameActive || smallBoards[boardIndex][cellIndex] || smallBoardWinners[boardIndex] || (nextBoard !== null && nextBoard !== boardIndex)) {
            return;
        }
    
        // 执行玩家移动
        e.target.style.animation = 'pulse 0.3s ease-out';//小动画
        smallBoards[boardIndex][cellIndex] = currentPlayer;//在小棋盘上记录玩家移动
        e.target.textContent = currentPlayer; //ui变化
        e.target.classList.add(currentPlayer.toLowerCase());
    
        // 检查小棋盘是否获胜
        const smallBoardWinner = checkSmallBoardWinner(boardIndex);
        if (smallBoardWinner) {
            smallBoardWinners[boardIndex] = smallBoardWinner;//记录小棋盘获胜者
            
            const smallBoardElement = document.querySelector(`.small-board[data-board-index="${boardIndex}"]`);//获取小棋盘上的棋子元素
            if (smallBoardWinner === 'X') {
                smallBoardElement.classList.add('won-by-x');
            } else {
                smallBoardElement.classList.add('won-by-o');
            }
        
            addWinningLine(boardIndex, smallBoardWinner);
        
            // 检查大棋盘是否获胜
            bigBoardWinner = checkBigBoardWinner();
            if (bigBoardWinner) {
                gameActive = false;
                showGameResult(bigBoardWinner);
                return;
            }
        }
    
        // 设置下一个必须下的小棋盘
        nextBoard = cellIndex;
    
        if (smallBoardWinners[nextBoard]) {
            nextBoard = null;
        } 
    
        // 切换玩家
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
    
    // 添加获胜线标记，主要在CSS里
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
    
    // 显示游戏结果
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
    
    // AI移动逻辑
    function makeAIMove() {
        if (!gameActive || currentPlayer !== aiSymbol) return;//判断是AI的回合
        
        const startTime = performance.now();
        const availableMoves = [];//可用移动数组
        
        // 收集所有可用的移动
        for (let i = 0; i < 9; i++) {
            if (nextBoard !== null && i !== nextBoard) continue;
            if (smallBoardWinners[i]) continue;
            
            for (let j = 0; j < 9; j++) {
                if (!smallBoards[i][j]) {
                    availableMoves.push({ boardIndex: i, cellIndex: j });
                }
            }
        }
        
        if (availableMoves.length === 0) return;//没有可用移动
        
        let selectedMove = null;
        
        // 优先检查AI是否有获胜的移动
        selectedMove = findWinningMove(availableMoves, aiSymbol);
        if (selectedMove) {
            console.log("AI找到了获胜的移动");
        }
        
        // 检查是否需要阻止玩家获胜
        if (!selectedMove) {
            selectedMove = findWinningMove(availableMoves, playerSymbol);
            if (selectedMove) {
                console.log("AI阻止了玩家的获胜");
            }
        }
        
        // 使用Minimax算法选择最佳移动
        if (!selectedMove) {
            console.log("AI使用简化的Minimax算法选择最佳位置");
            
            let bestScore = -Infinity;//最佳分数，初始为负无穷大
            let bestMove = null;//最佳移动，初始为null
            const movesToConsider = availableMoves.slice(0, Math.min(availableMoves.length, 15));//考虑的移动数组，最多15个
            
            for (const move of movesToConsider) {  //遍历每个移动
                smallBoards[move.boardIndex][move.cellIndex] = aiSymbol;//模拟AI移动
                
                const smallBoardWinner = checkSmallBoardWinner(move.boardIndex);  //检查那个小棋盘被占了
                const originalSmallBoardWinner = smallBoardWinners[move.boardIndex];  
                
                if (smallBoardWinner === aiSymbol) {  //如果小棋盘被AI占了记录这个小棋盘
                    smallBoardWinners[move.boardIndex] = aiSymbol; //
                }
                
                const bigBoardWinner = checkBigBoardWinner();
                if (bigBoardWinner === aiSymbol) {
                    selectedMove = move;
                    smallBoards[move.boardIndex][move.cellIndex] = '';
                    smallBoardWinners[move.boardIndex] = originalSmallBoardWinner;
                    break;
                }
                
                const nextBoardAfterMove = smallBoardWinner ? null : move.cellIndex;//判断下一个小棋盘
                
                const score = minimax( //递归调用Minimax函数
                    aiSearchDepth - 1, 
                    false, 
                    -Infinity, 
                    Infinity, 
                    nextBoardAfterMove
                );
                
                smallBoards[move.boardIndex][move.cellIndex] = ''; //撤销模拟移动
                smallBoardWinners[move.boardIndex] = originalSmallBoardWinner;
                
                if (score > bestScore) { //更新最佳分数和移动
                    bestScore = score;
                    bestMove = move;
                }
            }
            
            if (!selectedMove) { //如果没有直接获胜或阻止玩家获胜的移动，选择最佳移动
                selectedMove = bestMove;
            }
        }
        
        // 使用启发式策略
        if (!selectedMove) {
            selectedMove = findBestMove(availableMoves);
            console.log("AI使用进阶策略选择位置");
        }
        
        // 随机选择移动
        if (!selectedMove) {
            selectedMove = availableMoves[Math.floor(Math.random() * availableMoves.length)];
            console.log("AI随机选择位置");
        }
        
        // 执行选中的移动
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
    
    // Minimax+Alpha-Beta剪枝 递归
    function minimax(depth, isMaximizing, alpha, beta, currentNextBoard) {
        const bigBoardWinner = checkBigBoardWinner();
        
        if (depth === 0 || bigBoardWinner) {   //思考深度为0或大棋盘有赢家直接返回评估值
            return evaluateBoard(bigBoardWinner);
        }
        
        const availableMoves = [];
        
        for (let i = 0; i < 9; i++) {//收集所有可用移动
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
        // 限制考虑的移动数量以提高性能
        const movesToConsider = availableMoves.slice(0, Math.min(availableMoves.length, 10));
        
        if (isMaximizing) {
            let maxScore = -Infinity;
            
            for (const move of movesToConsider) {//遍历每个移动
                smallBoards[move.boardIndex][move.cellIndex] = aiSymbol;
                
                const smallBoardWinner = checkSmallBoardWinner(move.boardIndex);
                const originalSmallBoardWinner = smallBoardWinners[move.boardIndex];
                
                if (smallBoardWinner === aiSymbol) {
                    smallBoardWinners[move.boardIndex] = aiSymbol;
                }
                //确定下一个小棋盘
                const nextBoardAfterMove = smallBoardWinner ? null : move.cellIndex;
                //递归调用Minimax函数评估移动后的局面
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
                //检查小棋盘是否有赢家
                const smallBoardWinner = checkSmallBoardWinner(move.boardIndex);
                const originalSmallBoardWinner = smallBoardWinners[move.boardIndex];
                
                if (smallBoardWinner === playerSymbol) {
                    smallBoardWinners[move.boardIndex] = playerSymbol;
                }
                //确定下一个小棋盘
                const nextBoardAfterMove = smallBoardWinner ? null : move.cellIndex;
                //递归调用Minimax函数评估移动后的局面
                const score = minimax(depth - 1, true, alpha, beta, nextBoardAfterMove);
                //撤销模拟移动
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
    
    // 评估整个棋盘局面
    function evaluateBoard(bigBoardWinner) {
        if (bigBoardWinner === aiSymbol) {
            return 1000;
        } else if (bigBoardWinner === playerSymbol) {
            return -1000;
        } else if (bigBoardWinner === 'draw') {
            return 0;
        }
        
        let score = 0;
        
        for (let i = 0; i < 9; i++) { //评估每个小棋盘，根据占领情况加分或扣分
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
    
    // 评估单个小棋盘局面
    function evaluateSmallBoard(boardIndex) {
        const board = smallBoards[boardIndex];
        let score = 0;
        
        const positionWeights = [
            3, 2, 3,
            2, 4, 2,
            3, 2, 3
        ];
        //根据位置权重加分或扣分
        for (let i = 0; i < 9; i++) {
            if (board[i] === aiSymbol) {
                score += positionWeights[i];
            } else if (board[i] === playerSymbol) {
                score -= positionWeights[i];
            }
        }
        //评估行列斜线的潜在获胜可能性
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
            //只有AI棋子，根据棋子数加分
            if (aiCount > 0 && playerCount === 0) {
                score += aiCount * aiCount * 10;
            } else if (playerCount > 0 && aiCount === 0) {
                //只有玩家棋子，根据棋子数扣分
                score -= playerCount * playerCount * 10;
            }
        }
        //评估列的潜在获胜可能性
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
            //只有AI棋子，根据棋子数加分
            if (aiCount > 0 && playerCount === 0) {
                score += aiCount * aiCount * 10;
            } else if (playerCount > 0 && aiCount === 0) {
                score -= playerCount * playerCount * 10;
            }
        }
        
        let aiCount = 0;
        let playerCount = 0;
        for (let i = 0; i < 3; i++) {
            if (board[i * 4] === aiSymbol) { //评估主对角线
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
            if (board[i * 2 + 2] === aiSymbol) { //评估副对角线
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
    
    // 评估大棋盘潜在获胜可能性
    function evaluateBigBoardPotential() {
        let score = 0;
        
        for (let i = 0; i < 3; i++) { //评估行的潜在获胜可能性
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
        
        for (let i = 0; i < 3; i++) {//评估列的潜在获胜可能性
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
        for (let i = 0; i < 3; i++) { //评估主对角线的潜在获胜可能性
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
        for (let i = 0; i < 3; i++) { //评估副对角线的潜在获胜可能性
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
    
    // 寻找获胜移动
    function findWinningMove(availableMoves, player) {
        for (const move of availableMoves) { //检查是否有能直接赢得大棋盘的移动
            const { boardIndex, cellIndex } = move;
            
            smallBoards[boardIndex][cellIndex] = player;
            
            const smallBoardWinner = checkSmallBoardWinner(boardIndex);
            
            smallBoards[boardIndex][cellIndex] = '';
            
            if (smallBoardWinner === player) { //模拟该移动后检查大棋盘获胜者
                const originalWinner = smallBoardWinners[boardIndex];
                smallBoardWinners[boardIndex] = player;
                
                const bigBoardWinner = checkBigBoardWinner();
                
                smallBoardWinners[boardIndex] = originalWinner;
                
                if (bigBoardWinner === player) {
                    return move;
                }
            }
        }
        
        for (const move of availableMoves) {  //检查是否有能直接赢得小棋盘的移动
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
    
    // 启发式策略寻找最佳移动
    function findBestMove(availableMoves) {
        const positionWeights = [
            3, 2, 3,
            2, 4, 2,
            3, 2, 3
        ];
        
        let bestMove = null;
        let bestScore = -1;
        
        for (const move of availableMoves) { //评估每个移动的得分
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
    
    // 评估潜在获胜机会
    function evaluatePotentialWin(boardIndex, cellIndex, player) {
        smallBoards[boardIndex][cellIndex] = player;
        
        let potentialWins = 0;
        const board = smallBoards[boardIndex];

        // 检查行
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
        // 检查列
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
        // 检查主对角线
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
        // 检查副对角线
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
    
    // 评估对棋盘的控制
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
    
    // 评估下一步棋盘优势
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
    
    // 检查小棋盘获胜者
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
    
    // 检查大棋盘获胜者
    function checkBigBoardWinner() {
        //检查行
        for (let i = 0; i < 3; i++) {
            if (smallBoardWinners[i * 3] && smallBoardWinners[i * 3] !== 'draw' && 
                smallBoardWinners[i * 3] === smallBoardWinners[i * 3 + 1] && 
                smallBoardWinners[i * 3] === smallBoardWinners[i * 3 + 2]) {
                return smallBoardWinners[i * 3];
            }
        }
        //检查列
        for (let i = 0; i < 3; i++) {
            if (smallBoardWinners[i] && smallBoardWinners[i] !== 'draw' && 
                smallBoardWinners[i] === smallBoardWinners[i + 3] && 
                smallBoardWinners[i] === smallBoardWinners[i + 6]) {
                return smallBoardWinners[i];
            }
        }
        //检查对角线
        if (smallBoardWinners[0] && smallBoardWinners[0] !== 'draw' && 
            smallBoardWinners[0] === smallBoardWinners[4] && 
            smallBoardWinners[0] === smallBoardWinners[8]) {
            return smallBoardWinners[0];
        }
        //检查副对角线
        if (smallBoardWinners[2] && smallBoardWinners[2] !== 'draw' && 
            smallBoardWinners[2] === smallBoardWinners[4] && 
            smallBoardWinners[2] === smallBoardWinners[6]) {
            return smallBoardWinners[2];
        }
        //检查大棋盘是否平局
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