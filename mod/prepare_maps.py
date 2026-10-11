"""Preserve each stock map's own entry and zombie navigation scripts."""
from pathlib import Path
import hashlib,json,struct,zlib,re,os
from catalog import MAPS
root=Path(__file__).resolve().parent
game=Path(os.environ['WAW_GAME_DIR']).expanduser()
common=(root/'zone_source/nacht_garden.zone').read_text().splitlines()
common=[s for s in common if s not in ['rawfile,maps/nazi_zombie_prototype.gsc','rawfile,maps/_zombiemode_spawner.gsc']]
report={}
for mapname,profile,label in MAPS:
    original=game/'zone/english'/f'{mapname}.ff'
    backup=root/'backups/original-map'/f'{mapname}.ff'
    if backup.exists():original=backup
    data=zlib.decompress(original.read_bytes()[12:])
    patch=game/'zone/english'/f'{mapname}_patch.ff'
    sources=[(mapname,data)]
    if patch.exists():sources.insert(0,(mapname+'_patch',zlib.decompress(patch.read_bytes()[12:])))
    def read(name):
        marker=name.encode()+b'\0'
        for archive,zone in sources:
            at=zone.find(marker)
            if at<12:continue
            length=struct.unpack_from('<I',zone,at-8)[0]
            raw=zone[at+len(marker):at+len(marker)+length]
            if length>1000000 or not raw or zone[at+len(marker)+length]!=0:continue
            report[profile+'/'+name]={'archive':archive+'.ff','sha256':hashlib.sha256(raw).hexdigest()}
            return raw.decode().replace('\r\n','\n')
        raise ValueError(name)
    dest=root/'map-profiles'/profile/'maps';dest.mkdir(parents=True,exist_ok=True)
    name='maps/'+mapname+'.gsc';code=read(name)
    needle='maps\\_zombiemode::main('
    assert code.count(needle)==1
    code=code.replace(needle,'maps\\_nacht_garden::init();\n\t'+needle)
    (dest/Path(name).name).write_text(code)
    name='maps/_zombiemode_spawner.gsc';code=read(name)
    needle='self SetGoalPos( self.favoriteenemy.origin );'
    assert code.count(needle)==1
    code=code.replace(needle,'if ( !self maps\\_nacht_garden::garden_goal() )\n\t\t\t{\n\t\t\t\t'+needle+'\n\t\t\t}')
    (dest/Path(name).name).write_text(code)
    manifest=common+['rawfile,maps/'+mapname+'.gsc','rawfile,maps/_zombiemode_spawner.gsc']
    if mapname in ['nazi_zombie_sumpf','nazi_zombie_factory']:
        name='maps/_loadout.gsc'; code=read(name)
        needle='switch( self.entity_num)'
        assert code.count(needle)==1
        code=code.replace(needle,'garden_character = self.entity_num;\n\t\t\tplayers = get_players();\n\t\t\tif ( players.size == 1 ) garden_character = 3;\n\t\t\tswitch( garden_character )')
        (dest/Path(name).name).write_text(code)
        manifest.append('rawfile,'+name)
    name='maps/_zombiemode_weapons.gsc'; code=read(name)
    if mapname in ['nazi_zombie_sumpf','nazi_zombie_factory']:
        needle='get_player_index(player)\n{'
        assert code.count(needle)==1
        code=code.replace(needle,needle+'\n\tplayers = get_players();\n\tif ( players.size == 1 ) return 3; // Original Richtofen dialogue bank.')
    # Preserve stock special-item behavior for wall buys, box and Pack-a-Punch.
    for expression in ['current_weapon','user GetCurrentWeapon()','self GetCurrentWeapon()','player GetCurrentWeapon()']:
        old=expression+' == "mine_bouncing_betty"'
        code=code.replace(old,'( '+old+' || maps\\_nacht_garden::is_plant_weapon( '+expression+' ) )')
        old=expression+' != "mine_bouncing_betty"'
        code=code.replace(old,'( '+old+' && !maps\\_nacht_garden::is_plant_weapon( '+expression+' ) )')
    (dest/Path(name).name).write_text(code)
    manifest.append('rawfile,'+name)
    (root/'zone_source'/f'{profile}.zone').write_text('\n'.join(dict.fromkeys(manifest))+'\n')
(root/'map-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
print('Prepared four minimally patched stock map profiles.')
