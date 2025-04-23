import json
import os
from mahjong_ai import MahjongAI

class MahjongWeightTrainer:
    def __init__(self, mahjong_ai):
        self.mahjong_ai = mahjong_ai

    def train_weights(self, training_data_file):
        if not os.path.exists(training_data_file):
            print(f"训练数据文件 {training_data_file} 不存在。")
            return

        try:
            with open(training_data_file, 'r', encoding='utf-8') as file:
                training_data = json.load(file)

            for game in training_data:
                discard_pile = game.get('discard_pile', [])
                my_discards = game.get('my_discards', [])
                my_hand = game.get('my_hand', [])
                new_tile = game.get('new_tile', None)
                is_winning = game.get('is_winning', False)

                self.mahjong_ai.update_state(discard_pile, my_discards, my_hand, new_tile)
                tile_to_discard = self.mahjong_ai.choose_tile_to_discard()
                self.mahjong_ai.last_discarded_tile = tile_to_discard  # 显式设置 last_discarded_tile
                print(f"Before update experience: {self.mahjong_ai.tile_weights}")
                self.mahjong_ai.update_experience(is_winning)
                print(f"After update experience: {self.mahjong_ai.tile_weights}")

            print("权重训练完成，已保存更新后的权重。")
        except (json.JSONDecodeError, FileNotFoundError):
            print("读取训练数据文件时出错。")


if __name__ == "__main__":
    ai = MahjongAI()
    trainer = MahjongWeightTrainer(ai)
    training_data_file = "training_data.json"
    trainer.train_weights(training_data_file)