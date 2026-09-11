from src.common.schemas import PersonalInformation

p = PersonalInformation(full_name="Karan Lakhani", email="karan@example.com")
print(p)

p2 = PersonalInformation(full_name="Karan", email="not-a-real-email")
print(p2)