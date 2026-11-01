# Qwen3・ROS 2・Gazeboによる自然言語ロボット制御

## 1. 概要

ローカルLLM（Qwen3）を用いて、日本語の自然言語指示に基づく移動ロボットの動作制御を実装した。自然言語による指示をQwen3でJSON形式の動作計画に変換し、ROS 2を通じてGazebo上の差動二輪ロボットを制御する。

## 2. システム構成

自然言語指示 → Qwen3（Ollama） → JSON動作計画 → ROS 2 → Gazebo

- `generate_plan.py`：自然言語指示をQwen3で解釈し、JSON形式の動作計画を生成する。
- `motion_plan.json`：前進・旋回・停止の動作と、そのパラメータを記録する。
- `motion_controller.py`：JSONを読み込み、ROS 2の `/cmd_vel` トピックを通じて速度指令を送信する。

ROS 2とGazebo間の通信には `ros_gz_bridge` を使用する。

## 3. 使用環境

- Windows 11 / Docker Desktop
- ROS 2 Humble
- Gazebo Fortress
- Ollama / Qwen3-1.7B（`qwen3:1.7b`）
- Python 3

OllamaはWindows上で実行し、ROS 2とGazeboはDockerコンテナ内で実行した。


## 5. 実行例

一辺4 mの正方形を走行する日本語の指示から、Qwen3によって9動作のJSON計画を生成し、Gazebo上で実行した。動作計画は、前進4回（各4 m）、左90°旋回4回、停止1回から構成され、総動作時間は49秒である。制御は速度指令による開ループ方式であり、位置・姿勢のフィードバック制御は行っていない。

## 6. 外部リソース

Gazeboのロボットモデルおよびシミュレーション環境には、公式チュートリアルの `moving_robot.sdf` を無変更で使用した。

- [Gazebo公式 moving_robot.sdf](https://github.com/gazebosim/docs/blob/master/fortress/tutorials/moving_robot/moving_robot.sdf)
- [Gazeboドキュメントのライセンス](https://github.com/gazebosim/docs/blob/master/LICENSE)

