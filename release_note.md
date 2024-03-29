egGTFS ver.2.1 : release note 2023.12.1

# ver. 2.0 から 2.1 への変更点
## pip install への対応
egGTFS の pkg ディレクトリを指定することで、pip にて
インストールできるようにしました。
それに伴いディレクトリ構造が変更されています。

## routes\_jp.txt への対応を非公式に変更
GTFS-JP の第 3 版に対応するため、routes\_jp.txt へは
公式には対応しないようにしました。
ただし、後方互換性のために routes\_jp.txt が存在する場合は、
情報を読み書きするようにしています。

# ver. 1.0 から 2.0 への主な変更点
## 追加された新しい機能など
### ZIP ファイル形式への対応
　GTFS ファイルは .zip 形式で圧縮されたファイルとなりますが、
以前のバージョンではこれを展開して利用する必要がありました。
現在のバージョンより、.zip で圧縮されたままの形で
egGTFS を利用可能となりました。

### AreaRcet オブジェクトの追加
　緯度経度の矩形を表すオブジェクトです。
union, applyScale, getBounds メソッドを有しています。

#### union
　union(areaRect) で自分自身と引数 areaRect を含む矩形に
インスタンス自陣を拡張します。

#### applyScale
　applyScale(scaleFactor) にて、矩形領域を中心に与えられた
倍率だけ拡大します（1 未満の値を与えると矩形領域は縮小します）。

#### getBounds
　getBounds() で、インスタンスが示す矩形領域の
[[緯度の最小値,経度の最小値],[緯度の最大値,経度の最大値]] なる
リストを返します。
このリストは follium の fit\_bounds メソッドで利用できます。

### filter 関数の追加
　複数のレコードからなる構成ファイルマップオブジェクト（gtfs.trips 等）に対し、
フィルタ処理を施すことができるようになりました。

使用方法は filter(フィルタ関数 [,update=True]) です。

### drawShape 関数の追加
　与えられた follium のマップオブジェクトに対し、
与えられた shape ID のシェイプを上書きします。

使用方法は gtfs.drawShape(map,shapeID) です。

戻り値は、描画したシェイプを取り囲む最小の領域を表す
AreaRect オブジェクトのインスタンスです。


## 追加されたサンプルファイル
### ex\_filter.py 

filter 関数を使ったサンプルファイルです。
ある条件を設定したバス停を通過する、
全ての路線を抽出し、その路線からなる GTFS-JP ファイルを出力します。

### ex\_drawAllRoute.py

指定された GTFS に含まれる全ての路線を描画します。
ex\_filter.py と組み合わせることにより、
特定の条件を満たす路線のみを可視化します。


## 更新された機能など
### open メソッド
　展開された GTFS ではなく、ZIP ファイルで圧縮されたままの
GTFS ファイルを指定するように仕様が変更されました。

### getShapeMap メソッド
　egGTFS オブジェクトに実装されていた（注 1）getShapeMap メソッドの
機能拡張を行いました。
weight と color 引数にて、線の太さと色を指定できるようになりました。

```
import egGTFS
gtfs=egGTFS.open(someGtfsFilePath)
gtfs.getShapeMap(shpeID,weight=10,color="#CC1122")
```

weight と color を省略すると、
それぞれのデフォルト値として 8 と "#FF0000" が指定されます。

注 1：本メソッドは ver. 1.0 でも実装されていましたが、
その存在を公開していませんでした。
今回、仕様変更を行い、ライブラリ関数として公開できるようになったと
判断したため、公式メソッドとして公開することとしました。


## その他
　同梱しているサンプルファイルを見直し、
より利用しやすいように軽微な修正を行いました。

