"""Original PvZ sprite surfaces on the unchanged WaW Betty animation skeleton."""
import json,re,shutil

def prepare(base,portraits,image_asset,materials):
    root,raw=base.ROOT,base.RAW; native=base.TASK/'work/modtools'
    original=(base.TASK/'work/betty-export/raw/model_export/viewmodel_bbetty_mine_lod0.xmodel_export').read_text()
    skeleton=original[:original.index('NUMVERTS')]
    material_template=json.loads((base.TASK/'work/sumpf-materials/materials/mc/mtl_foliage_cod5_grass05c_card_static.json').read_text())
    weapon_fields=(base.TASK/'work/factory-weapons/weapons/mine_bouncing_betty').read_text().split('\\')
    stock=dict(zip(weapon_fields[1::2],weapon_fields[2::2]))
    props=(native/'raw/material_properties/ng_held_peashooter').read_bytes()
    from catalog import PLANTS
    from PIL import Image
    models=[];weapons=[];gdt=['{']
    (raw/'weapons').mkdir(exist_ok=True)
    for plant,label,_,_,_ in PLANTS:
        name='ng_held_'+plant;model=name;weapon='ng_seed_'+plant
        picture=portraits[plant].crop(portraits[plant].getbbox())
        width=12*picture.width/picture.height
        if width>14:height=12*14/width;width=14
        else:height=12
        image_asset(name,picture.resize((128,128),Image.Resampling.LANCZOS))
        material=json.loads(json.dumps(material_template))
        for texture in material['textures']:
            if texture['name']=='colorMap':texture['image']=name
        materials.remove(name);materials.append('mc/'+name)
        (raw/'materials/mc').mkdir(exist_ok=True)
        (raw/'materials/mc'/f'{name}.json').write_text(json.dumps(material,indent=2)+'\n')
        points=[(-width/2,0,0),(width/2,0,0),(width/2,0,height),(-width/2,0,height)]
        s=skeleton+'NUMVERTS 4\n'
        for i,(x,y,z) in enumerate(points):s+=f'VERT {i}\nOFFSET {x}, {y}, {z}\nBONES 1\nBONE 0 1.000000\n\n'
        s+='NUMFACES 2\n';uv=[(0,1),(1,1),(1,0),(0,0)]
        for tri in [(0,1,2),(0,2,3)]:
            s+='TRI 0 0 0 0\n'
            for i in tri:s+=f'VERT {i}\nNORMAL 0 -1 0\nCOLOR 1 1 1 1\nUV 1 {uv[i][0]} {uv[i][1]}\n'
        s+='NUMOBJECTS 1\nOBJECT 0 "pvz_original_sprite"\nNUMMATERIALS 1\n'
        s+=original[original.index('MATERIAL 0'):].replace('mc/mtl_weapon_bbetty_mine',name).replace('../images/weapon_bbetty_mine_c.dds','../images/'+name+'.dds')
        (native/'model_export'/f'{name}.xmodel_export').write_text(s)
        (native/'raw/material_properties'/name).write_bytes(props)
        gdt+=['"'+name+'" ( "xmodel.gdf" )','{','"type" "animated"','"filename" "'+name+'.xmodel_export"','"highLodDist" "1000000"','"collisionLOD" "None"','}']
        w=stock.copy()
        w.update(displayName=label,gunModel=model,worldModel='tag_origin',projectileModel='tag_origin',
                 ammoName=weapon,clipName=weapon,clipSize='1',sharedAmmoCapName=weapon,startAmmo='1',maxAmmo='1',sharedAmmoCap='1',
                 damage='0',minDamage='0',explosionInnerDamage='0',explosionOuterDamage='0',explosionRadius='0',
                 explosionRadiusMin='0',fuseTime='10',aifuseTime='10',projectileSpeed='0',projectileSpeedUp='0',projectileSpeedForward='0',
                 altWeapon='',killIcon='',hudIcon='',ammoCounterIcon='',bounceSound='',ammoPickupSound='',emptyFireSound='')
        # The harmless temporary grenade is deleted at its native throw notify.
        # Keep original hand/weapon animation references; remove explosive FX.
        for key in w:
            if 'effect' in key.lower() or key.lower().startswith('proj') and 'sound' in key.lower():w[key]=''
        (raw/'weapons'/weapon).write_text('WEAPONFILE'+''.join('\\'+k+'\\'+v for k,v in w.items()))
        models.append(model);weapons.append(weapon)
    gdt+=['}'];(native/'source_data/ng_plants.gdt').write_text('\n'.join(gdt)+'\n')
    (root/'held-plant-provenance.json').write_text(json.dumps({'sprite_source':'Installed PvZ reanimation art; cropped original idle pose','skeleton':'Original WaW viewmodel_bbetty_mine, unchanged bones and transforms','animation':'Original viewmodel_bbetty_* animation assets','geometry':'A transparent sprite display surface attached to j_gun; no invented 3D plant design','material':'Original mc_ambient_t0c0_sco cutout model technique','weapons':weapons},indent=2)+'\n')
    return models,weapons
