"""Doom-shroom integration, using Nacht's actual stock nuke power-up routine."""
from pathlib import Path
import argparse

def patch(s):
    if '// NG_DOOM_GAMEPLAY_V1' in s:return s
    assert 'level.ng_types = 10;' in s
    s=s.replace('level.ng_types = 10;','level.ng_types = 11;')
    s=s.replace('type >= 8 && GetDvar','( type == 8 || type == 9 ) && GetDvar')
    s=s.replace('level.ng_selection >= 8 && !self.ng_spot_water','( level.ng_selection == 8 || level.ng_selection == 9 ) && !self.ng_spot_water')
    s=s.replace('self.ng_spot_water && level.ng_selection < 8','self.ng_spot_water && level.ng_selection != 8 && level.ng_selection != 9')
    needle='    if ( type == 3 ) { p.ng_state = "fuse"; p.ng_until = GetTime()+900; }'
    assert needle in s;s=s.replace(needle,needle+'\n    if ( type == 10 ) { p.ng_state = "fuse"; p.ng_until = GetTime()+600; }')
    needle='    if ( IsDefined( self.ng_comparison_hold ) && self.ng_comparison_hold ) return;'
    assert needle in s;s=s.replace(needle,needle+'\n    if ( self.ng_type == 10 ) { self tick_doomshroom( now ); return; }')
    s+='''
// NG_DOOM_GAMEPLAY_V1: source animations, original PvZ sound, native WaW nuke.
tick_doomshroom( now )
{
    if ( now < self.ng_until ) return;
    if ( self.ng_state == "fuse" )
    {
        self.ng_state = "explode";
        self.ng_until = now+level.ng_clip_msec["doomshroom_explode"];
        self show_clip( "doomshroom_explode" );
        return;
    }
    if ( self.ng_state != "explode" ) return;
    self.ng_state = "spent";
    if ( IsDefined( level.zombie_powerups ) && IsDefined( level.zombie_powerups["nuke"] ) && IsDefined( level.zombie_powerups["nuke"].fx ) )
    {
        // Stock Nacht nuke reads origin and fx before its delayed zombie kills.
        // A struct survives plant cleanup without leaving an entity behind.
        powerup = SpawnStruct();
        powerup.origin = self.origin+(0,0,30);
        powerup.fx = level.zombie_powerups["nuke"].fx;
        level thread maps\\_zombiemode_powerups::nuke_powerup( powerup );
        PlaySoundAtPosition( "ng_loaded_doomshroom",self.origin );
        level thread doom_burst( self.origin,level.ng_owner.origin );
        PrintLn( "NACHT_GARDEN_DOOM_NUKE" );
    }
    else
    {
        level.ng_sun += 500;
        PrintLn( "NACHT_GARDEN_DOOM_NUKE_UNAVAILABLE_REFUNDED" );
    }
    level.ng_plants[self.ng_slot] = undefined;
    self remove_plant();
}

doom_burst( origin,viewer )
{
    visual = Spawn( "script_model",origin+(0,0,30) );
    visual SetModel( "tag_origin" );
    angles = VectorToAngles( viewer-origin );
    visual.angles = (0,angles[1],0);
    PlayFXOnTag( level.ng_clips["doomshroom_burst"],visual,"tag_origin" );
    wait( 1.6 );
    if ( IsDefined( visual ) ) visual Delete();
}
'''
    return s

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('script',type=Path);a=p.parse_args();a.script.write_text(patch(a.script.read_text()))
