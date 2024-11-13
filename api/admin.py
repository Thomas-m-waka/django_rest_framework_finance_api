from django.contrib import admin

from . models import * 
admin.site.register(Transaction)
admin.site.register(Debt)
admin.site.register(DebtRepayment)
admin.site.register(FinancialGoal)
admin.site.register(Account)
admin.site.register(Profile)
admin.site.register(Notification)

