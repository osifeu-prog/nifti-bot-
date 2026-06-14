import json

with open('lang.json', 'r', encoding='utf-8') as f:
    L = json.load(f)

new = {
    'mission_story': {
        'en': 'Why NIFTI?',
        'he': 'למה NIFTI?',
        'ru': 'Почему NIFTI?',
        'ar': 'لماذا NIFTI؟',
        'fr': 'Pourquoi NIFTI?',
        'es': '¿Por qué NIFTI?',
        'zh': '为什么选择 NIFTI？',
        'pt': 'Porquê NIFTI?'
    },
    'settings_title': {
        'en': 'Settings',
        'he': 'הגדרות',
        'ru': 'Настройки',
        'ar': 'الإعدادات',
        'fr': 'Paramètres',
        'es': 'Ajustes',
        'zh': '设置',
        'pt': 'Configurações'
    },
    'share_message': {
        'en': 'Share Your Card!',
        'he': 'שתף את הכרטיס!',
        'ru': 'Поделитесь картой!',
        'ar': 'شارك بطاقتك!',
        'fr': 'Partagez votre carte!',
        'es': 'Comparte tu tarjeta!',
        'zh': '分享您的名片！',
        'pt': 'Partilhe o seu cartão!'
    },
    'edit_name': {'en':'Edit Name','he':'ערוך שם','ru':'Изменить имя','ar':'تعديل الاسم','fr':'Modifier le nom','es':'Editar nombre','zh':'编辑姓名','pt':'Editar nome'},
    'edit_prof': {'en':'Edit Profession','he':'ערוך תחום','ru':'Изменить профессию','ar':'تعديل المهنة','fr':'Modifier profession','es':'Editar profesión','zh':'编辑职业','pt':'Editar profissão'},
    'edit_wallet': {'en':'Edit Wallet','he':'ערוך ארנק','ru':'Изменить кошелек','ar':'تعديل المحفظة','fr':'Modifier portefeuille','es':'Editar billetera','zh':'编辑钱包','pt':'Editar carteira'},
    'edit_price': {'en':'Edit Price','he':'ערוך מחיר','ru':'Изменить цену','ar':'تعديل السعر','fr':'Modifier le prix','es':'Editar precio','zh':'编辑价格','pt':'Editar preço'},
    'change_language': {'en':'Change Language','he':'החלף שפה','ru':'Сменить язык','ar':'تغيير اللغة','fr':'Changer de langue','es':'Cambiar idioma','zh':'更改语言','pt':'Mudar idioma'},
    'view_stats': {'en':'View Stats','he':'צפה בסטטיסטיקות','ru':'Статистика','ar':'عرض الإحصائيات','fr':'Voir les stats','es':'Ver estadísticas','zh':'查看统计','pt':'Ver estatísticas'},
    'level_up': {'en':'Level Up!','he':'עלית רמה!','ru':'Повышение уровня!','ar':'ترقية المستوى!','fr':'Niveau supérieur!','es':'¡Subiste de nivel!','zh':'升级了！','pt':'Subiu de nível!'},
    'settings_menu': {'en':'Settings','he':'הגדרות','ru':'Настройки','ar':'الإعدادات','fr':'Paramètres','es':'Ajustes','zh':'设置','pt':'Configurações'},
    'name_updated': {'en':'Name updated!','he':'השם עודכן!','ru':'Имя обновлено!','ar':'تم تحديث الاسم!','fr':'Nom mis à jour!','es':'¡Nombre actualizado!','zh':'姓名已更新！','pt':'Nome atualizado!'},
    'prof_updated': {'en':'Profession updated!','he':'התחום עודכן!','ru':'Профессия обновлена!','ar':'تم تحديث المهنة!','fr':'Profession mise à jour!','es':'¡Profesión actualizada!','zh':'职业已更新！','pt':'Profissão atualizada!'},
    'wallet_updated': {'en':'Wallet updated!','he':'הארנק עודכן!','ru':'Кошелек обновлен!','ar':'تم تحديث المحفظة!','fr':'Portefeuille mis à jour!','es':'¡Billetera actualizada!','zh':'钱包已更新！','pt':'Carteira atualizada!'},
    'invalid_wallet': {'en':'Invalid TON address','he':'כתובת ארנק לא חוקית','ru':'Неверный адрес TON','ar':'عنوان محفظة غير صالح','fr':'Adresse TON invalide','es':'Dirección TON inválida','zh':'TON 地址无效','pt':'Endereço TON inválido'}
}

for k, v in new.items():
    L[k] = v

with open('lang.json', 'w', encoding='utf-8') as f:
    json.dump(L, f, ensure_ascii=False, indent=2)

print('OK')
