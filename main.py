def read_file(path):
    with open(path, 'r') as file:
        return file.read()

# Example usage
if __name__ == "__main__":
    content = read_file('sample.txt')
    print(content)