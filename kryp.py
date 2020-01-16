# encrypts/decrypts the given string by adding 1 to the byte values of all chars in the string
def kryp(ori_string):
    krypet = ''
    for char in ori_string:
        c = ord(char)+1
        krypet += chr(c)
    return krypet

# encrypts/decrypts the given string by subtracting 1 to the byte values of all chars in the string
def dekryp(krypet):
    ori_string = ''
    for char in krypet:
        c = ord(char)-1
        ori_string += chr(c)
    return ori_string


if __name__ == '__main__':
    word = input("type desired word :)")
    print(f"original: {word}")
    word1 = kryp(word)
    print(f"+1: {word1}")
    word1 = dekryp(word1)
    word2 = dekryp(word)
    print(f"-1: {word2}")
    print(f"fixed: {word1}")
