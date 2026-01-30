import random

class CombatSystem:
    def __init__(self, output_func):
        self.log = output_func
        
    def battle(self, mc, enemy):
        self.log(f"\n【遭遇战】{mc.name} vs {enemy.name} ({enemy.sect})")
        self.log(f"敌方境界：{enemy.level_idx}阶 | 敌方战力：{enemy.attack}")
        self.log(f"{enemy.name}眼神冰冷：{enemy.get_dialogue('provoke')}")
        
        rounds = 0
        while mc.current_hp > 0 and enemy.current_hp > 0:
            rounds += 1
            # MC Turn
            skill = random.choice(mc.skills)
            damage = int(mc.attack * random.uniform(0.8, 1.2) - enemy.defense)
            if damage < 0: damage = 1
            
            # Critical hit / Instant Kill Logic
            if mc.attack > enemy.defense * 3:
                self.log(f"{mc.name}冷哼一声，只是随手使出一招【{skill}】。")
                self.log(f"“死！”")
                enemy.current_hp = 0
                self.log(f"{enemy.name}连惨叫都来不及发出，直接化为齑粉！(伤害: {damage*10}!!!)")
                break
                
            enemy.current_hp -= damage
            self.log(f"{mc.name}施展【{skill}】，造成了 {damage} 点伤害！{enemy.name}剩余血量：{max(0, enemy.current_hp)}")
            
            if enemy.current_hp <= 0:
                self.log(f"{enemy.name}满脸惊恐：{enemy.get_dialogue('dying')}")
                break
            
            # Enemy Turn
            enemy_skill = random.choice(enemy.skills)
            enemy_dmg = int(enemy.attack * random.uniform(0.8, 1.2) - mc.defense)
            if enemy_dmg < 0: enemy_dmg = 1
            
            # Dodge / System Block
            if random.random() < 0.3: # 30% dodge
                self.log(f"{enemy.name}打出【{enemy_skill}】，但{mc.name}身形如鬼魅般闪过，“太慢了。”")
            else:
                mc.current_hp -= enemy_dmg
                self.log(f"{enemy.name}狰狞一笑，【{enemy_skill}】轰在{mc.name}身上，造成 {enemy_dmg} 伤害！")
                
                # Low HP Trigger
                if mc.current_hp < mc.max_hp * 0.2:
                    self.log(f"【系统警告】宿主生命值过低！开启狂暴模式！")
                    mc.attack *= 2
                    self.log(f"{mc.name}双眼瞬间变得血红，气息暴涨！")

        if mc.current_hp > 0:
            self.log(f"战斗结束，{mc.name}胜！")
            loot = enemy.inventory
            if loot:
                self.log(f"摸尸环节：获得了 {', '.join(loot)}")
                mc.inventory.extend(loot)
            return True
        else:
            self.log(f"战斗结束，{mc.name}败... (系统：正在复活宿主...)")
            mc.current_hp = mc.max_hp # Revive logic
            return True # Plot armor always wins
