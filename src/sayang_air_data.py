
water_using = list()
water_using.append({
    "email": "and@gmail.com",
    "kuota_air": "90",
    "pemakaian_harian": 40,
    "hemat": 20000
})
water_using.append({
    "email": "putri@gmail.com",
    "kuota_air": "80",
    "pemakaian_harian": 36,
    "hemat": 16000
})
water_using.append({
    "email": "lidya@bangkit.academy",
    "kuota_air": "70",
    "pemakaian_harian": 20,
    "hemat": 10000
})
water_using.append({
    "email": "desy@bangkit.academy",
    "kuota_air": "90",
    "pemakaian_harian": 50,
    "hemat": 17000
})
water_using.append({
    "email": "rafli@bangkit.academy",
    "kuota_air": "90",
    "pemakaian_harian": 50,
    "hemat": 17000
})


def get_data_by_email(email):
    for data in water_using:
        if data["email"] == email:
            return data
    return False