import random
from novel_engine.data import loader

class Character:
    def __init__(self, is_protagonist=False):
        self.name = loader.names.get_person_name()
        self.is_protagonist = is_protagonist
        self.level_idx = 0
        self.max_hp = 100
        self.current_hp = 100
        self.attack = 10
        self.defense = 5
        self.skills = [loader.skills.get_skill_name() for _ in range(random.randint(1, 3))]
        self.sect = loader.sects.get_sect_name()
        self.inventory = [loader.items.get_item_name() for _ in range(random.randint(0, 2))]
        self.spirit_stones = random.randint(0, 100) # Economy system
        self.titles = []
        
        # Personality traits for dialogue generation
        self.arrogance = random.random() # 0-1, 1 is very arrogant
        self.cunning = random.random()
        
        if is_protagonist:
            self.name = "叶凌天" 
            self.arrogance = 0.5 
            self.max_hp = 1000
            self.attack = 50 
            self.spirit_stones = 0 # Start poor, get rich later
            self.inventory.append("神秘小瓶")
            self.titles.append("穿越者")

    def level_up(self):
        self.level_idx += 1
        self.max_hp *= 2
        self.current_hp = self.max_hp
        self.attack *= 2
        self.defense *= 2
        new_skill = loader.skills.get_skill_name()
        self.skills.append(new_skill)
        return new_skill

    def add_loot(self, items, stones):
        self.inventory.extend(items)
        self.spirit_stones += stones


    def get_dialogue(self, context="provoke"):
        if context == "provoke":
            if self.arrogance > 0.8:
                return f"“哼，{self.sect}办事，闲杂人等滚开！”"
            else:
                return f"“在下{self.name}，请指教。”"
        elif context == "dying":
            if self.arrogance > 0.8:
                return f"“不可能！我乃{self.sect}天骄，怎会死在你手里...”"
            else:
                return f"“技不如人，要杀要剐悉听尊便。”"
        return "“...”"

class Map:
    def __init__(self, level_range):
        self.name = random.choice(["黑风岭", "落日山脉", "乱星海", "葬神渊", "天元秘境"]) + " (Lv." + str(level_range) + ")"
        self.min_level = level_range
        self.npcs = []
        # Populate with random mobs
        for _ in range(10):
            npc = Character()
            npc.level_idx = level_range + random.randint(0, 2)
            self.npcs.append(npc)

class World:
    def __init__(self):
        self.maps = [Map(i*3) for i in range(10)] # Progressive difficulty
        self.protagonist = Character(is_protagonist=True)
        self.current_map_idx = 0
    
    def get_current_map(self):
        return self.maps[self.current_map_idx]
    
    def move_to_next_map(self):
        if self.current_map_idx < len(self.maps) - 1:
            self.current_map_idx += 1
            return True
        return False
