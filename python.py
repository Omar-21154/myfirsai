
# # # saat gosteren
# # sec_value = int(input('enter sec:'))

# # hour = sec_value // 3600
# # min = (sec_value % 3600 )//60
# # sec = sec_value % 60

# # print(f'sec:{sec},min:{min},hour:{hour}')


# # # uc reqemli cemi

# # num = int(input('input 3 reqemli number:'))

# # hundreds = num // 100 
# # onluq = (num // 10) % 10
# # teklik = num% 10 

# # print(f'reqenlerin cemi: {hundreds + onluq + teklik}')

# # #kredit

# # mebleg = float(input("Məbləğ: "))
# # faiz = float(input("Faiz: "))
# # il = float(input("İl: "))

# # ay_sayi = il * 12
# # yekun = mebleg * (1 + faiz / 100) ** ay_sayi

# # print(f"Yekun məbləğ: {yekun:.2f}")





# # #3 rəqəmli ədəd daxil edilir. Onu tərsinə çevirən proqram yazın.
# # # 379 yazılır ekrana 973 çıxmalıdır.

# # eded = int(input('eded daxil et:'))

# # eded_1 = eded % 10 
# # eded_2 = (eded // 10 )% 10 
# # eded_3 = eded // 100

# # ters_eded = (eded_1 * 100) + eded_2 * 10 +eded_3

# # print(f'senin ededinin tersi:{ters_eded}') 




# # 3

# num = int(input('TYPE numper:'))

# if num > 0 :
#     print(num)
# elif num < 0:
#     print(num * -1)
# else :
#     print(0)

from transformers import pipeline

# AI modelini yükləyirik (Text-generation - Mətn yaradılması)
ai_botu = pipeline('text-generation', model='gpt2')

def ai_ile_danis():
    print("AI Hazırdır! Çıxmaq üçün 'exit' yazın.")
    
    while True:
        istifadeci_suali = input("Siz: ")
        
        if istifadeci_suali.lower() == 'exit':
            break
        
        # AI cavab yaradır
        cavab = ai_botu(istifadeci_suali, max_length=50, num_return_sequences=1)
        
        print("\nAI Cavabı:")
        print(cavab[0]['generated_text'])
        print("-" * 30)

if __name__ == "__main__":
    ai_ile_danis()