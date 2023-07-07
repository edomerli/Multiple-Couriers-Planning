with open("inst21.dat", "r") as inputFile:
    m = int(inputFile.readline())
    n = int(inputFile.readline())
    l = []
    s = []
    D = []

    l.extend(list(map(int, inputFile.readline().split())))
    s.extend(list(map(int, inputFile.readline().split())))
    for i in range(n+1):
        D.append([])
        D[i].extend(list(map(int, inputFile.readline().split())))

with open("inst21.dzn", "w") as outputFile:
    outputFile.write(f"m = {m};\n")
    outputFile.write(f"l = {l};\n\n")
    outputFile.write(f"n = {n};\n")
    outputFile.write(f"s = {s};\n\n")

    outputFile.write("D =[|")
    for i in range(n+1):
        for j in range(n):
            outputFile.write(f" {D[i][j]},")
        outputFile.write(f" {D[i][n]}")
        outputFile.write("\n\t|")
    outputFile.write("];\n")
