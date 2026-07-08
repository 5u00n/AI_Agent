def main():
    board = [[' ' for _ in range(3)] for _ in range(3)]
    player = 'X'
    
    for i in range(9):
        print_board(board)
        print(f"Player {player}'s turn")
        
        while True:
            try:
                row = int(input("Enter row (0-2): "))
                col = int(input("Enter column (0-2): "))
                if row < 0 or row > 2 or col < 0 or col > 2:
                    print("Invalid input. Please enter numbers between 0 and 2.")
                    continue
                if board[row][col] == ' ':
                    board[row][col] = player
                    break
                else:
                    print("That position is already taken!")
            except ValueError:
                print("Please enter valid integers.")
        
        if check_winner(board, player):
            print_board(board)
            print(f"Player {player} wins!")
            return
        
        if is_board_full(board):
            print_board(board)
            print("It's a tie!")
            return
        
        player = 'O' if player == 'X' else 'X'
    
    print_board(board)
    print("It's a tie!")


def print_board(board):
    for row in board:
        print('|'.join(row))
        print('-' * 5)


def check_winner(board, player):
    # Check rows
    for row in board:
        if all(s == player for s in row):
            return True
    
    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2-i] == player for i in range(3)):
        return True
    
    return False

def is_board_full(board):
    return all(all(cell != ' ' for cell in row) for row in board)

if __name__ == "__main__":
    print('Welcome to Tic Tac Toe!')
    main()
