#!/usr/bin/env python3
import pandas as pd
import xlsxwriter

def create_sample_old():
    writer = pd.ExcelWriter('sample_old.xlsx', engine='xlsxwriter')
    
    hero_data = pd.DataFrame({
        'id': [1001, 1002, 1003],
        'name': ['战士', '法师', '弓手'],
        'hp': [1000, 600, 700],
        'attack': [150, 200, 180],
        'defense': [100, 50, 60]
    })
    hero_data.to_excel(writer, sheet_name='Hero', index=False)
    
    item_data = pd.DataFrame({
        'id': [2001, 2002, 2003],
        'name': ['铁剑', '布甲', '药瓶'],
        'price': [100, 50, 20],
        'type': ['武器', '防具', '消耗品']
    })
    item_data.to_excel(writer, sheet_name='Item', index=False)
    
    writer.close()
    print('已生成 sample_old.xlsx')

def create_sample_new():
    writer = pd.ExcelWriter('sample_new.xlsx', engine='xlsxwriter')
    
    hero_data = pd.DataFrame({
        'id': [1001, 1002, 1003, 1004],
        'name': ['战士', '法师', '游侠', '刺客'],
        'hp': [1100, 600, 750, 500],
        'attack': [150, 220, 180, 250],
        'defense': [100, 50, 60, 30],
        'speed': [50, 40, 70, 80]
    })
    hero_data.to_excel(writer, sheet_name='Hero', index=False)
    
    item_data = pd.DataFrame({
        'id': [2001, 2002, 2004],
        'name': ['钢剑', '布甲', '魔法卷轴'],
        'price': [200, 50, 150],
        'type': ['武器', '防具', '消耗品']
    })
    item_data.to_excel(writer, sheet_name='Item', index=False)
    
    skill_data = pd.DataFrame({
        'id': [3001, 3002],
        'name': ['火球术', '治疗术'],
        'damage': [200, 0],
        'heal': [0, 150]
    })
    skill_data.to_excel(writer, sheet_name='Skill', index=False)
    
    writer.close()
    print('已生成 sample_new.xlsx')

if __name__ == '__main__':
    create_sample_old()
    create_sample_new()
