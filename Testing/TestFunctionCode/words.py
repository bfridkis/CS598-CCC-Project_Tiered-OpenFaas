def get_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
        return text
    
def main():
    print(get_words('test.txt'))
    
if __name__ == "__main__":
    main()