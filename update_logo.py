import sys
import os

filepath = 'app.py'

try:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply substitutions
    replacements = [
        ('FutManager Pro MVP', 'PHP United FutebolManager'),
        ('FutManager Pro', 'PHP United FutebolManager'),
        ('FUTMANAGER PRO', 'PHP UNITED'),
        ('⚽ FUTMANAGER', '🐘 PHP UNITED'),
        ('page_icon=\"⚽\"', 'page_icon=\"🐘\"'),
        ('<div style=\"font-size:4rem;\">⚽</div>', '<div style=\"font-size:4rem;\">🐘</div>'),
        ('Sistema de gestão para seu grupo de futebol amador', 'Futebol Manager Oficial do PHP United'),
        ('#06080F', '#110D17'),
        ('#39ff14', '#B266FF'),
        ('#00f0ff', '#DFB3FF'),
        ('rgba(57, 255, 20', 'rgba(178, 102, 255'),
        ('rgba(0, 240, 255', 'rgba(223, 179, 255'),
        ('rgba(57,255,20', 'rgba(178,102,255'),
        ('rgba(0,240,255', 'rgba(223,179,255'),
        ('#00C853', '#6B21A8'),
        ('#1E88E5', '#9333EA'),
        ('#F5F7FA', '#F8F5FA')
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Substituições concluídas.")

except Exception as e:
    print("Erro durante substituição: ", e)
