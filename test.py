from dao import FraudTemplateDAO
a = FraudTemplateDAO().get_all()
for i in a:
    print(i.to_dict())