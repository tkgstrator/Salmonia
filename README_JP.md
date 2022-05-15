# Salmonia

Salmoniaはニンテンドーサーバからサーモンランのリザルトを取得し, Salmon Statsに自動的にアップロードするツールです.

## 必要要件

- Python3.7以上

## 導入方法

```zsh
python3 -m pip install -r requirements.txt
python3 main.py
```

現在、最新の一件のリザルトアップロードにしか対応していません.

### 機能

- [x] イカリング2認証
- [x] バージョンの自動更新
- [x] 認証情報ファイルの保存
- [ ] スタンドアロン
  - [ ] 最新のバイトIDの確認
  - [x] イカリング2から取得したリザルトのアップロード
  - [ ] イカリング2から取得して保存したリザルトのアップロード
  - [ ] リザルトの保存

### 環境

現在、ローカル環境にしか対応していません. 以下の行を変更することで異なる環境に対応できます.

https://github.com/tkgstrator/Salmonia/blob/c4373d95121781259a30a1b8134223bf8d4b6e08/salmonia.py#L98

### Salmon Stats Server

プライベートサーバを立てることもできます.

```zsh
git clone https://github.com/SalmonStats/api salmon-stats-sever
cd salmon-stats-server
make init
```

`docker-compose.yml`,`.env` を編集します.

別のウィンドウを開いて `make migrate` と `make up` と入力します.

