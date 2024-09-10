# egGTFS ver. 2.1.2
　egGTFS は、GTFS-JP 形式のファイルを読み書きする
Python ライブラリです。

# 対応している Python のバージョン
　開発ならびに動作確認は Python 3.11.2 にて行っていますが、
バージョン 3 系列の Python であれば動作すると思います。

# インストール方法
　pip install egGTFS としてインストールして下さい。

# 使い方
　egGTFS をインポートした後、egGTFS.open 関数を用いて
GTFS 情報を egGTFS に読み込ませます。

　egGTFS は、複数の GTFS 情報にも対応しています。
詳しい使用例は同梱されている samples/ex\_busHeatMap.py など、
ex\_ から始まるファイルを参照して下さい。

```
import egGTFS
# gtfs=egGTFS.open(GTFS ファイル）
gtfs=egGTFS.open('targetGtfsFile.zip')
```

以下、変数 gtfs に、とある GTFS-JP データが読み込まれているものとして説明を行います。

## 基本的な考え方
### 構成ファイルマップオブジェクト
　egGTFS では、GTFS-JP で策定されている
[https://www.gtfs.jp/developpers-guide/format-reference.html](https://www.gtfs.jp/developpers-guide/format-reference.html)
各種のファイルに格納されている情報には、

```
gtfs.拡張子なしのファイル名
```

としてアクセスできるように設計されています。

例えば、trips.txt に格納されている trips 情報にアクセスするには、
gtfs.trips プロパティ経由でアクセスします。

　これら trips などのオブジェクトを、本稿では、
**構成ファイルマップオブジェクト**と
呼ぶことにします。
GTFS として zip 形式でまとめられるファイルそれぞれに対応する
構成ファイルマップオブジェクトが存在します。

#### 構成ファイルマップオブジェクトの有効性
　構成ファイルマップオブジェクトには valid というプロパティを持っています。
このプロパティは、対応するファイルが存在する場合に True となります。
存在しなければ False が設定されています。

このプロパティはファイルの有無を示すものであり、
後述するレコードの有無を示すものではありませんので、
注意して下さい。


## レコード
　GTFS として zip 形式にまとめられる各 csv ファイルには、
行単位で情報が記述されており、これを本稿ではレコードと呼びます。
ファイルによっては、1 つのレコードのみが存在する
（または存在することが多い）ものと、
複数のレコードが存在するファイルがあります。
また、少し特殊な例としては、ファイルは存在するが
レコードが存在しない（0 レコードが存在する）場合もあります。

### 複数のレコードを持つ場合
#### インデクサ
　複数のレコードが存在するものについては、
対応する構成ファイルマップオブジェクトにはインデクサが用意されています。

　例えば trips では trip\_id にて一意に識別される情報が格納されています。
これらを取得する場合 - 例えば 'some-trip-id' という trip\_id を持つ trips 情報
（以下これを trips レコード等と呼びます）を取得するには、

```
gtfs.trip['some-trip-id']
```

とします。

　インデックス値として与えるものは一般的には文字列ですが、
ファイルに記述されている ID の値によっては数値として与える必要がある場合もあります。
どのようなインデックス値をあたえるべきかは、
取り扱う GTFS-JP ファイルの内容を確認して下さい。

　インデクサにより得られる値は、
インデックス値により一意にレコードが決まる場合は、
そのレコードの値を保持するレコードオブジェクトを返します。

レコードオブジェクトは、構成ファイルマップオブジェクト名の後に
\_record を付けたものです。
例えば trips 構成ファイルマップオブジェクトのインデクサにより
返されるものは trips\_record クラスのインスタンスとなります。

レコードオブジェクトのメンバ変数には、
各ファイルにおけるコラム名と同名のプロパティを有しています。
そのため、トリップ ID 'some-trip-id' を持つ trips レコードの
trip\_headsign 情報を取得するには、

```
gtfs.trips['some-trip-id'].trip_headsign
```

とします。

　構成ファイルマップオブジェクトによっては、
インデクサが配列を返す場合があります。
これは、当該ファイルの使用上、インデックス値に対応するレコードが
複数存在する場合などです。

インデクサにより返された値が、単一のレコードオブジェクトであるのか、
それともレコードオブジェクトの配列であるのかについては、
egGTFS.isArray 関数にて確認することができます
（配列ならば True を返します）。

　なお、指定したインデックス値に対応するレコードが存在しない場合は、
インデクサは None を返します。


#### イテレータ
　複数のレコードが存在すると期待される構成ファイルマップオブジェクトには、
イテレータが実装されています。
そのため次のようなコードにて、全レコードにアクセスできます。

trip.txt に格納されている情報全てにアクセスする場合：

```
for trip in gtfs.trips:
    print(str(trip))
```

### 単一のレコードのみを持つと想定されている場合
　agency など、単一のレコードのみからなると思われる構成ファイルマップオブジェクトでは、
直接それらのコラム名にて情報を取得できます。

```
# 事業者名（agency_name） を表示する
print(gtfs.agency.agency_name)
```

### レコードを持たない場合
　frequencies.txt のように、ファイルは存在するけれども
レコードが存在しないといった GTFS-JP ファイルも存在します。
この場合、既に説明しているとおり構成ファイルマップオブジェクトの valid プロパティは
True となります（対応するファイルは存在するので）。

しかし、hasRecord プロパティは False となります。

-----

# レコード数が 1 つのみとして実装されているもの
| 構成ファイルマップオブジェクト |
|--------------------------------|
| agency     |
| agency\_jp |
| feed\_info |

# 複数レコードをもつものとして実装されているもの
　補足情報欄に「あり」と記されているものについては、
この後に補足情報を記しています。

| 構成ファイルマップオブジェクト | インデクサのキー | 補足情報 |
|--------------------------------|------------------|----------|
| stops                          | stop\_id         |          |
| routes                         | routes\_id       |          |
| trips                          | trip\_id         |          |
| office\_jp                     | office\_id       |          |
| stop\_times                    | trip\_id         | あり     |
| calendar                       | service\_id      |          |
| calendar\_dates                | service\_id      |          |
| fare\_attributes               | fare\_id         |          |
| fare\_rules                    | route\_id        |          |
| shapes                         | shape\_id        | あり     |
| frequencies                    | trip\_id         |          |
| transfers                      | from\_stop\_id   |          |
| translations                   | trans\_id        |          |

## フィルタ機能
　複数のレコードを持つ構成ファイルマップオブジェクトには、
filter メソッドが用意されています。

使用方法は filter(フィルタ関数 [,update=True]) です。

　フィルタ関数は、残したいレコードの場合のみ True を返す関数のことです。
便宜上、フィルタ関数と表現していますが、lambda 式を直接記述しても構いません。
デフォルトでは、filter 関数を実行すると、対象の構成ファイルマップオブジェクトの
レコードがフィルタされたものに置き換えられます。
更新したくない場合は、filter(フィルタ関数,update=False) として使用して下さい。

具体的な使用方法は、サンプルプログラムとして ex\_filter.py を同梱していますので、
そちらを参照して下さい。

## stop\_times の補足情報
　一般的に、ひとつの trip\_id に対応する stop\_times 内のレコードは
複数となります。
そのため、インデクサを用いて取得される値は、
stop\_times\_record の配列となります。
これらの配列は stop\_sequence にて昇順に並び替えられています。

詳細はついては、以下の例を参考にして下さい（対話モードでの使用例）：

```
>>> seq=gtfs.stop_times['御所野線（通常）上り８']
>>> for t in seq: print(t.stop_sequence,t.stop_id)
...
seq= 1 stopID= akc0737
seq= 2 stopID= akc0016
seq= 3 stopID= akc0141
seq= 4 stopID= akc0143
seq= 5 stopID= akc0335
```

## shapes
shape\_id に対応するレコードは複数存在するため、
gtfs.shapes[shape\_id を示す文字列や数値] にて取得される値は
shapes\_record クラスのインスタンスの配列となります。
この配列はインデックス 0 から shape\_pt\_sequence が昇順になるよう
並び替えられています。

使用例：

```
>>> shapes=gtfs.shapes['100-1']
>>> print(len(shapes))
859
>>> print(str(shapes[800].shape_pt_sequence))
801
>>> print(str(shapes[801].shape_pt_sequence))
802
```

# egGTFS モジュールの関数
## version
　使用している egGTFS のバージョンを文字列で返します。

## open
　GTFS オブジェクトを生成します。
gtfs=egGTFS.open(gtfsFilePath) として使用します。
指定するファイルパスには GTFS ファイルの拡張子 .zip まで含めて指定して下さい。

## save
　GTFS オブジェクトの現在の状態を新たな GTFS-JP 形式で保存します。
gtfs.save(出力するファイル名) として使用します。
与えられたファイル名が .zip で修了していない場合、
自動的に .zip が追加されます。

## isArray
　配列か否かを返します。
egGTFS.isArray(x) などとして使用し、
もし変数 x が配列であれば True を、さもなければ False を返します。


# egGTFS クラスのメソッド
　gtfs=egGTFS.open(dirPathStr) として生成した gtfs オブジェクトが持つ
メソッドを示していきます。

## getStopPosSeqByTripID
　trip ID を引数に取り、その trip ID に関連する
バス停の位置（緯度,経度）の配列を返します。
返される配列は時間が昇順（最初の値が最も時間が早い）となるようになっています。

使用方法は gtfs.getStopPosSeqByTripID(tripID) です。

## getShapeIdByTripID
　trip ID を引数に取り、その trip ID の shape ID を返します。
shapes.txt が存在しない場合は None を返します。

使用方法は gtfs.getShapeIdByTripID(tripID) です。

## drawShape
　与えられた follium のマップオブジェクトに対し、
与えられた shape ID のシェイプを上書きします。

使用方法は gtfs.drawShape(map,shapeID[,weight=8,color="#FF0000"]) です。
weight は描画する線の太さを表し、
color は RRGGBB にて指定します。

戻り値は、描画したシェイプを取り囲む最小の領域を表す
AreaRect オブジェクトのインスタンスです。

## getShapeMap
　指定した shape ID の経路を描いた follium の地図オブジェクトを返します。

使用方法は gtfs.getShapeMap(shpeID[,weight=8,color="#FF0000"]) です。
weight は描画する線の太さを表し、
color は RRGGBB にて指定します。

詳しくは ex\_makeShapeHTML.py を参照して下さい。

## getTripMap
　指定した trip ID のシェイプならびにバス停を描画した
follium の地図オブジェクトを返します。

使用方法は gtfs.getTripMap(shpeID[,weight=8,color="#0000FF"]) です。
weight は描画する線の太さを表し、
color は RRGGBB にて指定します。

詳しくは ex\_drawTrip.py を参照して下さい。


## getPosListDistance
　与えられた [[lat1,lon1],[lat2,lon2], ... [latN,lonN]] の配列に対し、
[lat1,lon1] などを緯度・経度を表す組とみなし、
その配列が示す全行程の距離をメートル単位で返します。

## getBusPos
　trip ID と時刻を指定し、その時刻のバスの位置（緯度,経度）を返します。
shapes.txt が存在しない場合は None を返します。

使用方法は gtfs.getBusPos(tripID,timeStr) または
gtfs.getBusPos(tripID,hour,minute,second) です。
timeStr 形式を用いる場合は 'hh:mm:ss' 形式の文字列で与えて下さい。
hour,minute,second を指定する場合は、
それぞれの値は整数値を与えるようにして下さい。

## makeName
　follium を使ってマーカーを置く場合、
日本語が縦書きになってしまうので、それを回避するため、
与えられた文字列を span タグで包んで返します。

使用方法は gtfs.makeName(s) です。
