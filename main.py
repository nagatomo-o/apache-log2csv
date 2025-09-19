import argparse
import os
import re
import csv
from typing import List, Dict
from datetime import datetime

class LogFormat:
    def __init__(self, format: str='common', skip: bool=False):

        if format == 'common':
            self.format = '%h %l %u %t \"%r\" %>s %b'
        elif format == 'combined':
            self.format = '%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"'
        elif format == 'combinedio':
            self.format = '%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %I %O'
        else:
            self.format = format

        self.skip = skip

        self.fields_map = [
            {'key':'a', 'label':'RequestIP', 'pattern':r'(\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3})'},
            {'key':'A', 'label':'ServerIP', 'pattern':r'(\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3})'},
            {'key':'B', 'label':'Bytes', 'pattern':r'(\d+)'},
            {'key':'b', 'label':'Bytes', 'pattern':r'(\d+|-)'},
            {'key':'C', 'label':'Cookie', 'pattern':None},
            {'key':'D', 'label':'Duration', 'pattern':r'(\d+|-)'},
            {'key':'e', 'label':'Env', 'pattern':None},
            {'key':'f', 'label':'File', 'pattern':r'.+'},
            {'key':'h', 'label':'RemoteHost', 'pattern':r'(\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}|[\w\-\.]+)'},
            {'key':'H', 'label':'Protocol', 'pattern':r'(\w+)'},
            {'key':'i', 'label':'RequestHeader', 'pattern':None},
            {'key':'I', 'label':'ReceiveBytes', 'pattern':r'(\d+)'},
            {'key':'l', 'label':'RemoteLogName', 'pattern':r'([\w-]+|-)'},
            {'key':'m', 'label':'Method', 'pattern':r'(\w+|-)'},
            {'key':'n', 'label':'Memo', 'pattern':None},
            {'key':'o', 'label':'ResponseHeader', 'pattern':None},
            {'key':'O', 'label':'SendBytes', 'pattern':r'(\d+)'},
            {'key':'p', 'label':'Port', 'pattern':r'(\d+|-)'},
            {'key':'P', 'label':'ProcessID', 'pattern':r'(\d+|-)'},
            {'key':'q', 'label':'Query', 'pattern':r'(\?[^ ]+)'},
            {'key':'r', 'label':'Request', 'pattern':r'([A-Z]+ [^"]+(?: HTTP/[\d\.]{1,3})?|-)'},
            {'key':'s', 'label':'Status', 'pattern':r'(\d\d\d|-)'},
            {'key':'t', 'label':'Time', 'pattern':r'\[(\d{1,2}/\w{3}/\d{1,4}:\d\d:\d\d:\d\d [\-\+]\d\d\d\d)\]', 'convert': (lambda s: datetime.strptime(s,'%d/%b/%Y:%H:%M:%S %z').isoformat()) },
            {'key':'T', 'label':'Seconds', 'pattern':r'(\d+|-)'},
            {'key':'u', 'label':'RemoteUser', 'pattern':r'([\w-]+|-)'},
            {'key':'U', 'label':'URL', 'pattern':r'([^ ]+)'},
            {'key':'v', 'label':'VirtualHost', 'pattern':r'([\w\.\-]+)'},
            {'key':'V', 'label':'ServerName', 'pattern':r'([\w\.\-]+)'},
            {'key':'X', 'label':'ConnectionStatus', 'pattern':r'([\w\.\-]+)'},
        ]
        self.custom_fields = {
            'x-forwarded-for': r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:, \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})*|-)',
            'referer': r'([^"]+|-)',
            'user-agent': r'([^"]*|-)',
        }
        self.pattern = self.format
        self.labels = []
        self.fields = []

        matches = re.finditer(r'%(?:{([^}]+)}|>)?([A-Za-z])', self.format)
        for match in matches:
            field=None
            for f in self.fields_map:
                if f['key'] == match.group(2):
                    field = f
                    break

            if field == None:
                raise Exception(f"Unknown field keyword: {match.group(0)}")

            if match.group(1):
                pattern = self.custom_fields[match.group(1).lower()]
                label = match.group(1)
            else:
                pattern = field['pattern']
                label = field['label']

            self.labels.append(label)
            self.fields.append({
                'key': field['key'],
                'label': field['label'],
                'pattern': pattern,
                'convert': field['convert'] if 'convert' in field else (lambda s:s)
            })
            self.pattern = self.pattern.replace(match.group(0), pattern)
        print(self.pattern)

    def parse_line(self, line: str) -> Dict[str, str]:
        """ログ行を解析して、フィールド名と値の辞書を返す"""
        line = line.replace('\\"', '``')
        match = re.match(self.pattern, line)
        if match == None:
            if self.skip:
                return None
            else:
                raise Exception(f"Failed to parse line: {line} with pattern: {self.pattern}")

        if( len(match.groups()) != len(self.labels)):
            raise Exception(f"フィールド数が一致しません: {str(len(match.groups()))} != {str(len(self.labels))}")

        dict = {}
        for i, label in enumerate(self.labels):
            field = self.fields[i]
            value = match.group(i+1)
            value = value.replace('``', '"')
            if 'convert' in field:
                value = field['convert'](value)
            dict[label] = value

        return dict

def process_log_file(input_path: str, output_path: str, logFormat: LogFormat):
    """ログファイルを処理して CSV に変換"""

    with open(input_path, 'r', encoding='utf-8') as log_file, \
         open(output_path, 'w', encoding='utf-8', newline='\n') as csv_file:

        writer = csv.DictWriter(csv_file, fieldnames=logFormat.labels)
        writer.writeheader()

        for line in log_file:
            line = line.strip()
            if not line:
                continue
            record = logFormat.parse_line(line)
            if record == None:
                continue
            writer.writerow(record)

def merge_csv_files(csv_files: List[str], output_file: str, logFormat: LogFormat):
    """複数のCSVファイルを1つのファイルにマージする"""
    with open(output_file, 'w', encoding='utf-8', newline='\n') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=logFormat.labels)
        writer.writeheader()

        for csv_file in csv_files:
            with open(csv_file, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description='Apache アクセスログを CSV に変換')
    parser.add_argument('--input', required=True, help='入力ログファイル または ログファイルディレクトリ')
    parser.add_argument('--format', required=True, help='ログフォーマット(ApacheのLogFormat形式)')
    parser.add_argument('--merge', help='マージしたCSVの出力ファイル名')
    parser.add_argument('--skip', action='store_true', help='エラーが発生した行はスキップする')

    args = parser.parse_args()
    logFormat = LogFormat(args.format, args.skip)

    if os.path.isfile(args.input):
        # 単一ファイルの処理
        output_path = os.path.splitext(args.input)[0] + '.csv'
        process_log_file(args.input, output_path, logFormat)

    elif os.path.isdir(args.input):
        # ディレクトリ内の access_log* ファイルを処理
        processed_files = []

        for filename in os.listdir(args.input):
            if filename.startswith('access_log') and not filename.endswith('.csv') and not filename.endswith('.gz'):
                input_path = os.path.join(args.input, filename)
                output_path = os.path.splitext(input_path)[0] + '.csv'
                process_log_file(input_path, output_path, logFormat)
                processed_files.append(output_path)

        # マージオプションが指定されている場合、CSVファイルをマージ
        if args.merge and processed_files:
            merge_csv_files(processed_files, args.merge, logFormat)
            print(f"マージされたCSVファイルを作成しました: {args.merge}")

    else:
        print(f"Error: 指定されたパスが見つかりません: {args.input}")
        return 1

    return 0

if __name__ == '__main__':
    main()
