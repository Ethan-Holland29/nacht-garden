"""Apply the roster's original-effect Squash slam and non-resetting Wall-nut damage states."""
from pathlib import Path
import argparse

def patch(s):
    if 'NG_ROSTER_SLAM_V1' in s:return s
    old='''                        PlayFX( level._effect["headshot"],blood );
                        PlayFX( level._effect["headshot_nochunks"],blood );
                        PlayFX( level._effect["bloodspurt"],blood );'''
    assert old in s;s=s.replace(old,'                        plant_blood_burst( blood );')
    old='''            variant = target walnut_variant();
            target animate_once( variant+"twitch" );'''
    assert old in s;s=s.replace(old,'''            // Change damaged artwork only when its health stage changes.
            // Restarting a blink on every bite interrupted the continuous loop.
            target show_clip( target idle_clip() );''')
    needle='        p = level.ng_plants[i];\n        distance = Distance( self.origin, p.origin );'
    assert needle in s;s=s.replace(needle,'''        p = level.ng_plants[i];
        if ( p.ng_type == 7 && p.ng_state != "idle" && p.ng_state != "look" ) continue;
        distance = Distance( self.origin, p.origin );''')
    a=s.index('    // 1800 base damage,');b=s.index('    if ( caption != "" )',a)
    damage=s[a:b]
    damage=damage.replace('        if ( tr["fraction"] >= 0.99 ) z DoDamage( damage,z.origin+(0,0,36),level.ng_owner );', '''        if ( tr["fraction"] >= 0.99 )
        {
            if ( bloody ) plant_blood_burst( z.origin+(0,0,42) );
            z DoDamage( damage,z.origin+(0,0,36),level.ng_owner );
        }''')
    s=s[:a]+'    self plant_area_damage( radius,damage,false );\n'+s[b:]
    helper='''// NG_ROSTER_SLAM_V1: original Nacht blood assets, shared by bite and slam.
plant_blood_burst( origin )
{
    if ( !IsDefined( level._effect ) ) return;
    if ( IsDefined( level._effect["headshot"] ) ) PlayFX( level._effect["headshot"],origin );
    if ( IsDefined( level._effect["headshot_nochunks"] ) ) PlayFX( level._effect["headshot_nochunks"],origin );
    if ( IsDefined( level._effect["bloodspurt"] ) ) PlayFX( level._effect["bloodspurt"],origin );
}

plant_area_damage( radius,damage,bloody )
{
    center = self.origin+(0,0,20);
'''+damage+'''}

'''
    s=s.replace('plant_explosion( radius,damage,caption )\n{',helper+'plant_explosion( radius,damage,caption )\n{')
    a=s.index('// Squash commits to a nearby target,');b=s.index('\ntick_kelp( now )',a)
    s=s[:a]+'''// Original PvZ look/jump/land sprite poses travel on a native WaW mover.
// The target floor is locked before takeoff; geometry traces bound the arc.
tick_squash( now )
{
    if ( self.ng_state == "idle" )
    {
        victim = self nearest_zombie( 120 );
        if ( !IsDefined( victim ) ) return;
        self.ng_target = victim;
        self.ng_state = "look";
        self.ng_until = now+500;
        self show_clip( "squash_attack" );
        PlaySoundAtPosition( "ng_loaded_squash_hmm",self.origin );
        return;
    }
    if ( now < self.ng_until ) return;
    if ( self.ng_state == "look" )
    {
        self.ng_landing = self.origin;
        victim = self.ng_target;
        if ( IsDefined( victim ) && IsAlive( victim ) && Distance( self.origin,victim.origin ) < 180 )
        {
            tr = BulletTrace( self.origin+(0,0,25),victim.origin+(0,0,25),false,self );
            floor = BulletTrace( victim.origin+(0,0,30),victim.origin-(0,0,60),false,self );
            if ( tr["fraction"] >= 0.99 && floor["fraction"] < 1 && floor["normal"][2] > 0.85 )
                self.ng_landing = floor["position"];
        }
        lift = 96;
        roof = BulletTrace( self.ng_landing+(0,0,4),self.ng_landing+(0,0,150),false,self );
        if ( roof["fraction"] < 1 && roof["position"][2]-self.ng_landing[2]-50 < lift )
            lift = roof["position"][2]-self.ng_landing[2]-50;
        roof = BulletTrace( self.origin+(0,0,4),self.origin+(0,0,150),false,self );
        if ( roof["fraction"] < 1 && roof["position"][2]-self.origin[2]-50 < lift )
            lift = roof["position"][2]-self.origin[2]-50;
        // Stay within low ceilings instead of clipping through map geometry.
        if ( lift < 12 )
        {
            self.ng_state = "idle";
            self show_clip( "squash_idle" );
            return;
        }
        tr = BulletTrace( self.origin+(0,0,lift+24),self.ng_landing+(0,0,lift+24),false,self );
        if ( tr["fraction"] < 0.99 ) self.ng_landing = self.origin;
        self.ng_state = "rise";
        self.ng_until = now+350;
        apex = self.ng_landing+(0,0,lift+level.ng_anchor[7]);
        if ( IsDefined( self.ng_visual ) ) self.ng_visual MoveTo( apex,0.35,0,0.15 );
        return;
    }
    if ( self.ng_state == "rise" )
    {
        self.ng_state = "hover";
        self.ng_until = now+100;
        return;
    }
    if ( self.ng_state == "hover" )
    {
        self.ng_state = "slam";
        self.ng_until = now+150;
        if ( IsDefined( self.ng_visual ) ) self.ng_visual MoveTo( self.ng_landing+(0,0,level.ng_anchor[7]),0.15,0.1,0 );
        return;
    }
    if ( self.ng_state == "slam" )
    {
        self.origin = self.ng_landing;
        self.ng_state = "land";
        self.ng_until = now+level.ng_clip_msec["squash_land"];
        self show_clip( "squash_land" );
        PlaySoundAtPosition( "ng_loaded_floop",self.origin );
        self plant_area_damage( 105,1800,true );
        return;
    }
    // The landing animation finishes after the hit, without a second blast.
    level.ng_plants[self.ng_slot] = undefined;
    self remove_plant();
}
''' +s[b:]
    return s

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('script',type=Path);a=p.parse_args()
    a.script.write_text(patch(a.script.read_text()))
    print('Applied original-animation Squash mover, blood impact and Wall-nut loop fix.')
