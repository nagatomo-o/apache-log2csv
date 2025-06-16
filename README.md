# Apache AccessLog 変換

## 概要

Apacheのアクセスログを項目ごとに識別してCSV形式に変換します

## 使い方

### 基本的な使い方
```bash
python main.py --input=<PATH> --format=<FORMAT>
```

### オプション
- `--input=<PATH>`    : 入力ログファイルまたはログファイルディレクトリのパス
- `--format=<FORMAT>` : ApacheのLogFormat形式でログフォーマットを指定
- `--merge=<FILE>`    : ディレクトリ内のログファイルを変換後、指定したファイルにマージ
- `--skip`            : エラーが発生した行をスキップ

### 使用例
1. 単一ファイルの変換:
```bash
python main.py --input=/var/log/apache2/access_log --format="%h %l %u %t \"%r\" %>s %b"
```

2. ディレクトリ内のログファイルを変換してマージ:
```bash
python main.py --input=/var/log/apache2/ --format="%h %l %u %t \"%r\" %>s %b" --merge=merged_logs.csv
```

3. カスタムログフォーマットでの変換:
```bash
python main.py --input=/var/log/apache2/access_log --format="%{X-Forwarded-For}i %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %D %h"
```

### 注意事項
- 入力パスは絶対パスまたは相対パスで指定可能
- ログフォーマットはApacheのLogFormatディレクティブと同じ形式で指定
- ディレクトリを指定した場合、`access_log`で始まるファイルのみが処理対象
- `.csv`または`.gz`で終わるファイルは処理対象外

## 仕様

### ファイル入出力

1. 引数の入力がログファイルの場合
    1. 同じディレクトリに`access_log.csv`形式で出力する
    2. 同じファイルが存在する場合には上書きを行う

2. 引数の入力がログファイルディレクトリの場合
    1. ディレクトリ内の`access_log`で始まり、`.csv`または`.gz`で終わらないファイルを対象にそれぞれ変換処理を行う
    2. 同じディレクトリに`ファイル名.csv`形式で出力する
    3. 同じファイルが存在する場合には上書きを行う

### 変換処理

1. 引数のログフォーマットを解析する
2. 各ファイルの各行を解析してログフォーマットに基づき分割する
3. CSV形式で出力する
