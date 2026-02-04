from novel_engine.data.database import NPCData

def test():
    print("Testing NPCData...")
    name = NPCData.get_name("M", "00s")
    print(f"Generated Name: {name}")
    
    print(f"Families: {NPCData.FAMILIES[:3]}...")
    print(f"Archetypes: {NPCData.ARCHETYPES[:2]}...")
    print(f"Teacher Profiles: {NPCData.TEACHER_PROFILES[:2]}...")
    
    assert len(NPCData.FAMILIES) > 0
    assert len(NPCData.QUIRKS) > 0
    assert len(NPCData.FLAWS) > 0
    assert len(NPCData.ARCHETYPES) > 0
    
    print("✅ NPCData tests passed!")

if __name__ == "__main__":
    test()
