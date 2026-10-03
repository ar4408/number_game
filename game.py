import random


answer = random.randint(1, 100)
attempts = 0

print("数当てゲームへようこそ！")
print("1から100までの数字を当ててください。")

while True:
    guess_text = input("数字を入力してください: ")

    if not guess_text.isdigit():
        print("数字を入力してください。")
        continue

    guess = int(guess_text)

    if guess < 1 or guess > 100:
        print("1から100までの数字を入力してください。")
        continue

    attempts += 1

    if guess < answer:
        print("もっと大きい数字です。")
    elif guess > answer:
        print("もっと小さい数字です。")
    else:
        print(f"正解です！{attempts}回で当たりました。")
        break