#!/usr/bin/env python
# coding: utf-8

# [MIT License]
# 
# PyAudio is distributed under the MIT License:
# Copyright (c) 2006 Hubert Pham
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# [PIL Software License]
# 
# The Python Imaging Library (PIL) is
# Copyright © 1997-2011 by Secret Labs AB
# Copyright © 1995-2011 by Fredrik Lundh
# By obtaining, using, and/or copying this software and/or its associated documentation, you agree that you have read, understood, and will comply with the following terms and conditions:
# Permission to use, copy, modify, and distribute this software and its associated documentation for any purpose and without fee is hereby granted, provided that the above copyright notice appears in all copies, and that both that copyright notice and this permission notice appear in supporting documentation, and that the name of Secret Labs AB or the author not be used in advertising or publicity pertaining to distribution of the software without specific, written prior permission.
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# [3-clause BSD License]
# 
# Copyright (c) 2014-2017, Anthony Zhang <azhang9@gmail.com>
# All rights reserved.
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# In[1]:


#  #VOICEVOXを忘れずに起動する事！
# # 各種ライブラリインストール
    
# !pip install --upgrade pip
# !pip install pyaudio    
# !pip install openai
# !pip install --upgrade openai 
# !pip show openai

# !pip install SpeechRecognition
# !pip install Pillow

# !pip install pyinstaller#実行ファイル作成用
# !pip install opencv-python


# In[2]:


#chatGPT
import openai
openai.api_key = ""


# In[3]:


#合成した音声を出力するための関数を定義（逆転マルチスレッド）
import pyaudio
import wave
import time
import threading
import queue

# Queueオブジェクトの生成
q = queue.Queue()
q.put("n")            
def play_stream(file_name):
    file_name += ".wav"
    file_name = folder_path + file_name
    CHUNK = 1024

    wf = wave.open(file_name, 'rb')
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    data = wf.readframes(CHUNK)#１音目を発声
    c = 0
    agent_now = "n"
    while data:
        global rms
        rms= 0.0
        for i in range(0, len(data), 2):
            sample = int.from_bytes(data[i:i+2], byteorder="little", signed=True)
            rms += sample ** 2
        rms /= CHUNK
        rms = rms ** 0.5
        if c % 4 == 0:
            if rms > 500 and agent_now == "n":
                agent_now = "u"
                q.put("u")
            elif rms < 1000 and agent_now == "u":
                agent_now = "n"
                q.put("n")

        stream.write(data)
        data = wf.readframes(CHUNK)
        c += 1
    stream.stop_stream()
    stream.close()
    p.terminate()
    q.put("playend")


# In[4]:


message_count = 0
def UpdateMessageLog (text, tag):
    global message_count
    message_count += 1
    if message_count > 2:
        canvas.move("input", 0, -scrh / 4) # 会話履歴を上にずらす
        canvas.move("res", 0, -scrh / 4)
#    if len(text) > 39 : text = text[:37] + "..." # 文字を切るLinux用
    if len(text) > 60 : text = text[:58] + "..." # 文字を切るWindows用
    if tag == "input":
        if message_count == 1:
            imagey=scrh * 1 / 4
        else:
            imagey = scrh * 2 / 4
        canvas.create_image(
            scrw * 77 / 100,
            imagey, 
            anchor=tk.N,
            image=black_box,
            tag=tag
        )
        canvas.create_text(
            scrw * 77 / 100,
            imagey + scrh * 3 / 100,
            text=text[:15] + "\n" + text[15:30] + "\n" + text[30:45] + "\n" + text[45:60],
            fill="white",
            font=("HG丸ｺﾞｼｯｸM-PRO", canvas.winfo_height() // 40, "bold"),
            anchor="n",
            tag=tag
        )

    elif tag == "res":
        canvas.create_image(scrw*62/100, scrh*2/4, anchor=tk.N, image=black_box,  tag=tag)
        canvas.create_text(
            scrw*62/100,
            scrh*(2/4+3/100),
            text=text[:15] + "\n" + text[15:30] + "\n" + text[30:45] + "\n" + text[45:60],
            fill="white",
            font=("HG丸ｺﾞｼｯｸM-PRO", canvas.winfo_height()//40, "bold"),
            anchor="n",
            tag=tag
        )

    print(message_count)
    canvas.update_idletasks()


# In[5]:


import string
def is_half_width(text):  # imputTextが半角か否かを判定する関数
    half_width_chars = string.ascii_letters + string.digits + string.punctuation
    for char in text:
        if char not in half_width_chars:
            return False
    return True


# In[6]:


import speech_recognition as sr

def record_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("話してください...")
            r.adjust_for_ambient_noise(source)  # ノイズの調整
            audio = r.listen(source, timeout=1)  # 何秒の沈黙を許すか    
            print("音声認識結果: " + r.recognize_google(audio, language='ja-JP'))
            q.put(r.recognize_google(audio, language='ja-JP'))
        except sr.WaitTimeoutError:
            q.put("タイムアウトしました。")
        except sr.UnknownValueError:
            q.put("音声を理解できませんでした。") 
        except sr.RequestError:
            q.put("音声認識サービスでエラーが発生しました。") 


# In[7]:


def on_configure(event):
    global scrh, scrw
    #print("Window size:", event.width, event.height)
    scrh = event.height
    scrw = int(scrh*3/2)
    
    # for widget in widget_list:
    canvas.config(width=scrw, height=event.height)
    canvas.update()


# In[8]:


def key_handler(e):
    if e.keycode == 13 :  # Enterキーでwindows用
        q.put("key")
    elif e.keycode == 27:  # 9Escキーでwindows用
        root.destroy()  # ウィンドウを終了する

#     if e.keycode == 36 :  # EnterキーでLinux用
#         q.put("key")
#     elif e.keycode == 9:  # 9EscキーでLinux用
#         root.destroy()  # ウィンドウを終了する 


# In[9]:


#VOICEVOXのアプリにクエリを飛ばして合成してもらう関数を定義
import json
import requests
def generate_wav(text, speaker=1, file_name="audio"):
    file_name += ".wav"
    file_name = folder_path + file_name
    host = 'localhost'
    port = "50021"
    params = (
        ('text', text),
        ('speaker', speaker),
    )
    response1 = requests.post(
        f'http://{host}:{port}/audio_query',
        params=params
    )
    headers = {'Content-Type': 'application/json',}
    response2 = requests.post(
        f'http://{host}:{port}/synthesis',
        headers=headers,
        params=params,
        data=json.dumps(response1.json())
    )
    wf = wave.open(file_name, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(24000)
    wf.writeframes(response2.content)
    wf.close()
    q.put("voicevoxend")


# In[10]:


# whileループ結合
import os
import time
import cv2
import tkinter as tk
from PIL import Image, ImageTk
import queue
import pyaudio
import wave
import threading


# Queueオブジェクトの生成
q = queue.Queue()            

# GUIセットアップーーーーーーーーーーーーーーーーーーーーーーー
# メインウィンドウ生成
root = tk.Tk()
folder_path = "./resources/"
root.overrideredirect(True)  # ウィンドウバーを消す#windows用
root.iconphoto(False, tk.PhotoImage(file=folder_path + 'icon.png'))#  byヒザフライ様 #ウィンドウアイコン設定
root.title("PersonalAssistant")
#root.attributes('-fullscreen', True)  # フルスクリーン

root.config(bg="black") # 背景を黒にする # windows用
root.attributes("-transparentcolor", "black") # 黒を透過する # windows用
# Linuxではウィンドウの透過はこのライブラリではできない

# ディスプレイサイズを取得してスクリーンのサイズを決める
scrh = int(root.winfo_screenheight()*97/100)
scrw = int(scrh*3/2)
root.geometry(f"{scrw}x{scrh}+{0}+{root.winfo_screenheight()*97//100-scrh}")  # debug用
#root.geometry(f"{scrw}x{scrh}+{root.winfo_screenwidth()-scrw}+{root.winfo_screenheight()*95//100-scrh}")  # Windows用
# root.geometry(f"{scrw}x{scrh}+{root.winfo_screenwidth()-scrw}+{root.winfo_screenheight()-scrh}")  # Linux用
# root.geometry(f"{scrw}x{scrh}+{root.winfo_screenwidth()-scrw}+{root.winfo_screenheight()//2-scrh}")  # DualLinux用
# root.geometry(f"{scrw}x{scrh}+0+0")  # 通常用



# 画像を読み込む
agent_u = Image.open(folder_path + "雨晴はう立ち絵ver1.20_u.png")  # by 縁若そばこ様 agentに改名
agent_n = Image.open(folder_path + "雨晴はう立ち絵ver1.20_n.png")  # ボディー込みby 縁若そばこ様
# agent_ikari = Image.open(folder_path + "TT_Tachie_ikari.png")  # by 捨て犬A様 agentに改名
# agent_yorokobi = Image.open(folder_path + "TT_Tachie_yorokobi.png")  # ボディー込みby 捨て犬A様
# agent_konran = Image.open(folder_path + "TT_Tachie_konran.png")  # by 捨て犬A様 agentに改名
# agent_warai = Image.open(folder_path + "TT_Tachie_warai.png")  # ボディー込みby 捨て犬A様喜怒哀楽
alpha = Image.open(folder_path + "alpha.png")
back = Image.open(folder_path + "icon.png")  # by：ヒザフライ様
black = Image.open(folder_path + "black.png")
box = Image.open(folder_path + "massagebox.png")
black_box = Image.open(folder_path + "massagebox_black.png")
entryBox = Image.open(folder_path + "entryBox.png")
send = Image.open(folder_path + "send.png")
send = send.convert('RGBA')

# 画像のサイズを調整
image_width, image_height = agent_u.size  # 立ち絵画像のサイズ取得
agent_height = int(scrh)  # 画像の高さをディスプレイの1/3の大きさに指定
agent_width = int(agent_height*image_width/image_height)  # 高さに横幅を合わせる
box_height = int(scrh/5)
box_width = int(box_height*1600/500)
entryBox_width = int(scrw*55/100)
entryBox_height = int(entryBox_width*400/2700*5/6)
send_height = int(entryBox_height*80/100)

# 画像をリサイズ
agent_u = agent_u.resize((agent_width, agent_height))
agent_n = agent_n.resize((agent_width, agent_height))
# agent_yorokobi = agent_yorokobi.resize((agent_width, agent_height))
# agent_ikari = agent_ikari.resize((agent_width, agent_height))
# agent_warai = agent_warai.resize((agent_width, agent_height))
# agent_konran = agent_konran.resize((agent_width, agent_height))
back = back.resize((scrw, scrh))
alpha = alpha.resize((scrw, scrh))
black = black.resize((scrw, scrh))
box = box.resize((box_width, box_height))
black_box = black_box.resize((box_width, box_height))
entryBox = entryBox.resize((entryBox_width, entryBox_height))
send = send.resize((send_height, send_height))

# ImageTkオブジェクトを作成
agent_u = ImageTk.PhotoImage(agent_u)
agent_n = ImageTk.PhotoImage(agent_n)
# agent_yorokobi = ImageTk.PhotoImage(agent_yorokobi)
# agent_ikari = ImageTk.PhotoImage(agent_ikari)
# agent_warai = ImageTk.PhotoImage(agent_warai)
# agent_konran = ImageTk.PhotoImage(agent_konran)
back = ImageTk.PhotoImage(back)
alpha = ImageTk.PhotoImage(alpha)
black = ImageTk.PhotoImage(black)
# box = ImageTk.PhotoImage(box)
black_box = ImageTk.PhotoImage(black_box)
entryBox = ImageTk.PhotoImage(entryBox)
send = ImageTk.PhotoImage(send)



# OpenCVで動画ファイルを読み込む
#cap = cv2.VideoCapture(folder_path + 'breathAlphaHalfSpeed.mp4')  # 動画読み込み

# キャンバスの作成
canvas = tk.Canvas(root, width=scrw, height=scrh, bg='black', highlightthickness=0)
canvas.pack()

# Canvasを作成して画像を表示
# canvas.create_image(scrw/2, scrh/2, image=back, tag="back")  # 背景透過中
# canvas.create_image(scrw/2, scrh/2, image=alpha, tag="alpha")  # 背景透過中
# agent = canvas.create_image(-scrw/20, 0, anchor=tk.NW, image=agent_n, tags="n_tag")
canvas.create_image(scrw*62/100, 0, anchor=tk.N, image=black_box, tag="res")

# 最初のagent_n画像オブジェクトを作成
# agent_n_obj = canvas.create_image(
#     -scrw / 20,
#     0,
#     anchor=tk.NW,
#     image=agent_n,
#     tags="n_tag"
# )
# agent_u_obj = canvas.create_image(
#     -scrw / 20,
#     0,
#     anchor=tk.NW,
#     image=agent_u,
#     tags="u_tag"
# )
# agent_yorokobi_obj = canvas.create_image(
#     -scrw / 20,
#     0,
#     anchor=tk.NW,
#     image=agent_yorokobi,
#     tags="yorokobi_tag"
# )
# agent_ikari_obj = canvas.create_image(
#     -scrw / 20,
#     0,
#     anchor=tk.NW,
#     image=agent_ikari,
#     tags="ikari_tag"
# )
# agent_konran_obj = canvas.create_image(
#     -scrw / 20,
#     0,
#     anchor=tk.NW,
#     image=agent_konran,
#     tags="konran_tag"
# )
# agent_warai_obj = canvas.create_image(
#     -scrw / 20,
#     0,
#     anchor=tk.NW,
#     image=agent_warai,
#     tags="warai_tag"
# )

prevFrame = None
entryBox_width = int(scrw * 55 / 100)
entryBox_height = int(entryBox_width * 400 / 2700 * 5 / 6)

entryBox = Image.open(folder_path + "entryBox.png")       
entryBox = entryBox.resize((entryBox_width, entryBox_height))

entryBox = ImageTk.PhotoImage(entryBox)

entry = tk.Entry(
    root,
    fg="white",
    width=23,
    bg="#232323",
    bd=0,
    highlightthickness=0,
    font=("HG丸ｺﾞｼｯｸM-PRO", entryBox_height * 3 // 10, "bold")
)        
entry.place(x=scrw * 47 / 100, y=scrh * 92 / 100)  # 枠あり
#entry.place(x=scrw * 56 / 100, y=scrh * 90 / 100)  # full


# In[11]:


def openai_request():
    if log_on == True:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system","content": role},
                {"role": "assistant","content": log},  # 前回の対話を引き継ぎ
                {"role": "user","content": inputText},
            ],
        )
    else:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system","content": role},
                {"role": "user","content": inputText},
            ],
        )
    res = res["choices"][0]["message"]["content"]
    q.put(res)


# In[12]:


entry.bind("<KeyPress>", key_handler)
# "メイドとして、ご主人様に対して２０字以内で返答をしてください。"
# "ご主人様を恋愛的に好きなメイドとして、ご主人様に対する返答をしてください。"
# 返答の最初に、返答文に対応する【笑い】、【怒り】、【混乱】、【喜び】、【冷静】のどれかを付けて出力してください。
role = "メイドとして、ご主人様に対して２０字以内で返答をしてください。"

setting = False
log = ""
speaker = 10  #雨晴はうさん  #48#50#14 # デフォルトの声設定

root.bind("<Configure>", on_configure)  # window情報取得開始。並列処理可
phase = ""
res = ""
backup = False
log_on = False
emotion = ""
playend = True
generate_focus = 0
play_focus = 0
res_list = [0]
generate_comp = True
play_comp = True
generate_mode = False
while True:
    # queueの内容を保存
    if q.empty():
        q_content = ""
    else:
        q_content = q.get()
    if q_content == "key":
        entryText=entry.get()  #  入力ボックスの文字列を読み込み
        entry.delete(0, "end")  #  入力ボックスの内容をクリア
        if setting == True:  # セッティングモードの時
            setting = False        
            inputText = entryText
            UpdateMessageLog(inputText, "input")  # ユーザーの発言内容表示
            if inputText.startswith("change_persona:"):
                inputText = inputText.replace("change_persona:", "", 1)
                role = inputText
                res = "人格設定を変更しました。"
    #         elif inputText.startswith("touka_on"):
    #             res = "背景を透過します。（現在は未実装です）"
    #             phase = ""  
    #         elif inputText.startswith("touka_off"):
    #             res = "背景を表示します。（現在は未実装です）"
    #             phase = ""  # フェーズ初期化
            elif inputText.startswith("speaker_id:"):
                inputText = inputText.replace("speaker_id:", "", 1)
                if inputText.isdigit():  # 数字のとき（全角でもVOICEVOXはOK）
                    speaker=inputText
                    res = "これからこの声で話します。"
                else:
                    res = "数字で指定してください。"
            elif inputText == "log_on":
                log_on = True
                log = ""
                res = "あなたとの会話を思い出しながら話します。"
            elif inputText == "log_off":
                log_on = False
                log = ""
                res = "これまでのことは忘れて、これからはあなたの一言に対して話します。"
            else:
                res = "書式が間違っています。再度設定を入力してください。"
                setting = True
            phase = ""
        else:
            if entryText == "" and openai.api_key != "":  # APIキーが入力されるまでは音声認識しない
                thread = threading.Thread(target=record_audio)
                thread.start()
                phase = "recognition"
            else :  # APIキーが空かテキスト入力された時
                inputText = entryText
                phase = "confirmation"
    elif phase == "recognition":  # inputTextの内容が音声認識中でまだ定まっていない
        inputText = q_content
        if inputText == "":
            pass
        elif inputText == "タイムアウトしました。":
            thread = threading.Thread(target=record_audio)
            thread.start()
        elif inputText == "音声を理解できませんでした。":
            #phase = "confirmation"
            thread = threading.Thread(target=record_audio)
            thread.start()
        elif inputText == "音声認識サービスでエラーが発生しました。":
            phase = "confirmation"
        else:  # 正しく音声認識できた時
            phase = "confirmation"
    elif phase == "confirmation":  # inputTextの内容は確定し　てる
        UpdateMessageLog(inputText, "input")  # ユーザーの発言内容表示
        phase = "control"        
    elif phase == "control":  # セッティングモードでないとき
        if inputText == "/setting":
            res = "設定モードを起動しました。人格の命令文、声、履歴の設定ができます。"
            phase = ""
            setting = True
        else:
            if inputText == "":  # inputTextが空でAPIキーも未入力の時
                res = "APIキーを入力してください"
                phase = ""
            elif openai.api_key == "":  # APIキーが未入力の時inutTextの中身はAPIキーの候補
                if is_half_width(inputText):
                    openai.api_key = inputText  # APIキーを読み込む
                    res = ""  # APIキー検証のためにクリア
                    phase = ""
                    try:  # マルチスレッド化で一瞬のかくつきを無くせる？
                        res = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user","content": inputText},],
                            max_tokens=1,
                        )
                        res = "APIキーを認識しました。"
                    except openai.error.AuthenticationError as error:
                        openai.api_key = ""  # 有効ではないAPIキーをクリア
                        res = "そのAPIキーは有効ではありません。再度入力をお願いします。"
                else:
                    res = "APIキーは半角です。"
                    phase = ""
            elif inputText == "音声を理解できませんでした。":
                res = "ノイズが大きいか発音が不明瞭なため、何と言っているか聞き取れませんでした。"
                phase = ""
            elif inputText == "音声認識サービスでエラーが発生しました。":
                res = "外部音声認識サービスへのアクセスに失敗しました。"
                phase = ""  # フェーズ初期化人格の命令文、声、履歴の設定ができます。
            else:  # まったくエラーが無く、APIキーがあるとき
                print(inputText)  # APIキーは表示されない
                # 対話生成開始
                thread = threading.Thread(target=openai_request)
                thread.start()
                phase = "waitres"   
    elif phase == "waitres":
        if q_content != "":
            res = q_content
            if "【喜び】" in res:
                emotion = "yorokobi"
                res = res.replace("【喜び】", "", 1)
            elif "【怒り】" in res:
                emotion = "ikari"
                res = res.replace("【怒り】", "", 1)
            elif "【混乱】" in res:
                emotion = "konran"
                res = res.replace("【混乱】", "", 1)
            elif "【笑い】" in res:
                emotion = "warai"
                res = res.replace("【笑い】", "", 1)
            elif "【冷静】" in res:
                emotion = "reisei"
                res = res.replace("【冷静】", "", 1)

            log += inputText
            log += res
            phase = ""
    if res != "":
        print(res)
        UpdateMessageLog(res, "res")  # アシスタントの発言内容表示
        if speaker == 48 and res == "APIキーは半角です。":
            thread = threading.Thread(target=play_stream, args=(res,))#編集中
            thread.start()  
            res = ""
            phase = "playing"
        elif speaker == 48 and res == "外部音声認識サービスへのアクセスに失敗しました。":#要追記
            thread = threading.Thread(target=play_stream, args=(res,))
            thread.start()
            res = ""
            phase = "playing"
        elif speaker == 48 and res == "そのAPIキーは有効ではありません。再度入力をお願いします。":#要追記
            thread = threading.Thread(target=play_stream, args=(res,))
            thread.start()
            res = ""
            phase = "playing"
        elif speaker == 48 and res == "設定モードを起動しました。人格の命令文、声、履歴の設定ができます。":#要追記
            thread = threading.Thread(target=play_stream, args=(res,))
            thread.start()
            res = ""
            phase = "playing"
        elif speaker == 10 and res == "APIキーは半角です。":
            thread = threading.Thread(target=play_stream, args=(str(speaker)+"_"+res,))#編集中
            thread.start()  
            res = ""
            phase = "playing"
        elif speaker == 10 and res == "外部音声認識サービスへのアクセスに失敗しました。":#要追記
            thread = threading.Thread(target=play_stream, args=(str(speaker)+"_"+res,))
            thread.start()
            res = ""
            phase = "playing"
        elif speaker == 10 and res == "そのAPIキーは有効ではありません。再度入力をお願いします。":#
            thread = threading.Thread(target=play_stream, args=(str(speaker)+"_"+res,))
            thread.start()
            res = ""
            phase = "playing"
        elif speaker == 10 and res == "設定モードを起動しました。人格の命令文、声、履歴の設定ができます。":#
            thread = threading.Thread(target=play_stream, args=(str(speaker)+"_"+res,))
            thread.start()
            res = ""
            phase = "playing"
        else:
            # 一括生成パターン
            generate_mode = True
            phase = "playing"
            
#             # 分割生成パターン
#             generate_mode = True  # セリフを音声合成するフラグ
#             # 句点と読点で分割
#             res = res.replace("。", "、")
#             res_list = res.split("、")
#             #res_list = 1  # ノイズ軽減のために分割なし
#             res = ""
#             generate_focus = 0
#             generate_comp = False
#             phase = "playing"
    
    # 以降描画    声生成後動画だけ重くなる
    # 1フレームずつ読み込む
#     ret, frame = cap.read()
#     if not ret:  # 読み込めなかったとき
#         cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # 動画の最初に戻る
#         ret, frame = cap.read()
#         backup = True
        
    # OpenCVのBGR画像をPPMフォーマットに変換
#     img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     img = Image.fromarray(img)
#     img = img.resize((scrh, scrh))
#     img = ImageTk.PhotoImage(img)

    if prevFrame == None:
        # キャンバス上に新しいフレームの画像を表示
#        img_obj = canvas.create_image(-scrw / 20, 0, image=img, anchor=tk.NW)  # 動画の１フレーム描画
        agent_u_obj = canvas.create_image(
            -scrw / 20,
            0,
            anchor=tk.NW,
            image=agent_u,
            tags="u_tag"
        )
        agent_n_obj = canvas.create_image(
            -scrw / 20,
            0,
            anchor=tk.NW,
            image=agent_n,
            tags="n_tag"
        )
        prevFrame = True
        black_box_obj = canvas.create_image(scrw*62/100, 0, anchor=tk.N, image=black_box, tag="res")
        text="あなたの言葉を読んだり聞いたりできます。\nあなたのAPIキーを教えてください。"
        canvas.create_text(scrw*62/100, scrh*5/100,text=text[:15] + "\n" + text[15:30] + text[30:45] + "\n" + text[45:60], fill="white", font=("HG丸ｺﾞｼｯｸM-PRO", scrh//40, "bold") , anchor="n", tag = "res")#windows用
        #canvas.create_text(scrw*62/100, scrh*5/100,text=text[:13] + "\n" + text[13:26] + "\n" + text[26:], fill="white", font=("HG丸ｺﾞｼｯｸM-PRO", scrh//40, "bold") , anchor="n", tag = "res")#Linux用
        entryBox_obj = canvas.create_image(scrw*72/100, scrh*89/100, anchor=tk.N, image=entryBox)  # 枠あり
        #entryBox_obj = canvas.create_image(scrw*72/100, scrh*87/100, anchor=tk.N, image=entryBox)  # full

    else:
        # 既存のagent_n画像オブジェクトを取得し、configを使って画像を更新
#        canvas.itemconfig(img_obj, image=img)  # 動画再生
        if backup == True:
            canvas.create_image(
                -scrw / 20,
                0,
                anchor=tk.NW,
                image=agent_n,
                tags="n_tag"
            )
            backup = False
    if phase == "playing":
        if generate_mode:
            # 一括生成パターン
            generate_thread = threading.Thread(target=generate_wav, args=(res, speaker,))
            generate_thread.start()
            res = ""
            generate_mode = False
                    
        if q_content == "voicevoxend":
            play_thread = threading.Thread(target=play_stream, args=("audio",))
            play_thread.start()

                        
#             # 分割生成パターン
#             # 最初の句を生成する
#             if (generate_focus == 0 or q_content == "voicevoxend") and not generate_comp:
#                 if generate_focus == 1:  # 一句生成し終わってたら
#                     play_focus = 0  # 再生開始
#                     playend = True
#                     play_comp = False
#                 if generate_focus >= len(res_list) - 1 and generate_focus > 0:  # 最後の句まで生成したとき
#                     generate_comp = True
#                 else:
#                     generate_thread = threading.Thread(target=generate_wav, args=(res_list[generate_focus], speaker, str(generate_focus)))
#                     generate_thread.start()
#                     generate_focus += 1
                
                
#             if q_content == "playend":
#                 playend = True
#                 # 一句目か再生が終わった　　かつ　再生のフォーカスが生成を超えないか生成が終了している　かつ　再生が完了していない
#             if (play_focus == 0 or playend) and (play_focus < generate_focus - 1 or generate_comp) and not play_comp:  # 本当は-1しなくてもいいはずだが、ファイルの読み込みに失敗する
# #                 print(f"listlen:{len(res_list)}")
# #                 print(f"generate:{generate_focus}")
# #                 print(f"play_focus:{play_focus}")
# #                 print(f"comp:{generate_comp}")

#                 if play_focus >= len(res_list) - 1 and play_focus > 0:  # 最後の句まで再生したとき
#                     play_comp = True
#                     generate_mode = False
# #                     for i in range(play_focus):
# #                         if os.path.exists(f"{i}.wav"):
# #                             os.remove(f"{i}.wav")

#                 else:
#                     if os.path.exists(f"{folder_path + str(play_focus)}.wav"):
#                         play_thread = threading.Thread(target=play_stream, args=(str(play_focus),))
#                         play_thread.start()
#                         play_focus += 1
#                         playend = False
                
                
        if q_content == "u":
            canvas.create_image(
                -scrw / 20,
                0,
                anchor=tk.NW,
                image=agent_u,
                tags="u_tag"
            )
        elif q_content == "n" or q_content == "playend":
            canvas.create_image(
                -scrw / 20,
                0,
                anchor=tk.NW,
                image=agent_n,
                tags="n_tag"
            )
#         if emotion == "yorokobi":
#             canvas.create_image(
#                 -scrw / 20,
#                 0,
#                 anchor=tk.NW,
#                 image=agent_yorokobi,
#                 tags="yorokobi_tag"
#             )
#         elif emotion == "ikari":
#             canvas.create_image(
#                 -scrw / 20,
#                 0,
#                 anchor=tk.NW,
#                 image=agent_ikari,
#                 tags="ikari_tag"
#             )
#         elif emotion == "konran":
#             canvas.create_image(
#                 -scrw / 20,
#                 0,
#                 anchor=tk.NW,
#                 image=agent_konran,
#                 tags="konran_tag"
#             )
#         elif emotion == "warai":
#             canvas.create_image(
#                 -scrw / 20,
#                 0,
#                 anchor=tk.NW,
#                 image=agent_warai,
#                 tags="warai_tag"
#             )
#         if q_content == "playend":
#             canvas.create_image(
#                 -scrw / 20,
#                 0,
#                 anchor=tk.NW,
#                 image=agent_n,
#                 tags="n_tag"
#             )
        

    canvas.update()# キャンバスを更新
    
# メモリ解放
cap.release()
cv2.destroyAllWindows()


# In[15]:


get_ipython().system('pyinstaller PersonalAssistant-v1.1.1.py --onefile')

get_ipython().system('pyinstaller PersonalAssistant-v1.1.1.spec')

