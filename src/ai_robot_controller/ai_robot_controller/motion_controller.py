
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import json
from pathlib import Path


class MotionController(Node):

    def __init__(self):
        super().__init__('motion_controller')

        # ロボットへの速度指令を送信するPublisherを作成。
        # Twist：速度指令のメッセージ型
        # /cmd_vel：速度指令を送信するトピック名
        # /cmd_velは速度指令（Twistメッセージ）を送受信するROS 2のトピック（論理的な通信路）。
        # 10：QoSの履歴キュー深さ
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # (並進速度 [m/s], 角速度 [rad/s], 継続時間 [s])
        # ROS 2のパラメータ plan_file を宣言し、デフォルト値を motion_plan.json とする。
        self.declare_parameter("plan_file", "motion_plan.json")
        
        # パラメータからファイル名を取得
        self.plan_file = Path(self.get_parameter("plan_file").value)
        
        # JSONを読み込み、動作計画に変換
        self.plan = self.load_plan()

        self.step = 0  # 現在実行しているアクションの番号
        self.step_start = None
        self.timer = self.create_timer(0.05, self.update)  # 0.05秒ごとに self.update() を呼び出すタイマーを登録

    def load_plan(self):
        # # ROS 2パラメータで指定されたJSONファイルを読み込む
        with self.plan_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

            plan = []

        for action in data["actions"]:
            action_type = action["type"]
            duration = float(action["duration"])

            if action_type == "forward":
                linear = float(action["speed"])
                angular = 0.0

            elif action_type == "turn":
                linear = 0.0
                angle_deg = float(action["angle_deg"])
                angular = math.radians(angle_deg) / duration

            elif action_type == "stop":
                linear = 0.0
                angular = 0.0

            else:
                raise ValueError(f"Unknown action type: {action_type}")

            plan.append((linear, angular, duration))

        return plan
    
    def publish_velocity(self, linear, angular):
        # Twistメッセージを生成
        # msg.linear: (v_x, v_y, v_z), msg.angular: (omega_x, omega_y, omega_z)
        # 速度指令は固定された世界座標系ではなく、ロボット自身の座標系で指定する。
        # x軸は常にロボットの前方を向くため、旋回するとx軸も一緒に回転する。
        # angular.zは鉛直軸まわりの角速度（反時計回りが正）。
        msg = Twist()
        msg.linear.x = float(linear)  # ロボット前方の並進速度 [m/s]
        msg.angular.z = float(angular)  # 鉛直軸まわりの角速度 [rad/s]
        self.publisher.publish(msg)  # /cmd_velに速度指令を送信

    def update(self):
        now = self.get_clock().now()

        # シミュレーション時刻が有効になってから開始時刻を設定する
        if self.step_start is None:
            if now.nanoseconds == 0:
                return

            self.step_start = now
            self.get_logger().info(
                f"Motion started at {now.nanoseconds / 1e9:.3f} s"
            )

        # すべての動作が終了している場合
        if self.step >= len(self.plan):
            self.publish_velocity(0.0, 0.0)
            self.timer.cancel()
            self.get_logger().info("Motion completed.")
            return

        # 現在の動作を取得
        linear, angular, duration = self.plan[self.step]

        # 現在の動作の経過時間
        elapsed = (now - self.step_start).nanoseconds / 1e9

        # 指定時間が経過したら次の動作へ
        if elapsed >= duration:
            self.step += 1
            self.step_start = now

            # 最後の動作が終了した場合
            if self.step >= len(self.plan):
                self.publish_velocity(0.0, 0.0)
                self.timer.cancel()
                self.get_logger().info("Motion completed.")
                return

            # 次の動作を取得
            linear, angular, duration = self.plan[self.step]

        # 速度指令を送信
        self.publish_velocity(linear, angular)


def main(args=None):
    # ROS2の通信機能を初期化
    # args=Noneの場合、コマンドライン引数を利用
    rclpy.init(args=args)

    # イベントループのようなもの
    node = MotionController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_velocity(0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
