// Nacht Garden: new integration logic only. Art comes from the two installed games.
#include common_scripts\utility;
#include maps\_utility;

init()
{
    if ( IsDefined( level.ng_plants ) ) return;
    maps\_nacht_garden_assets::init();
    level.ng_pea_fx = level.ng_clips["pea"];
    PrecacheModel( "tag_origin" );
    level.ng_plants = [];
    level.ng_limit = 18;
    level.ng_sun = 200;
    level.ng_selection = -1;
    level.ng_types = 10;
    level.ng_ready = [];
    for ( i = 0; i < level.ng_types; i++ ) level.ng_ready[i] = 0;
    level.ng_page = 0;
    level.ng_last_hit_sound = 0;
    SetDvar( "ng_action", "" );
    level thread session();
}

session()
{
    level endon( "intermission" );
    while ( !IsDefined( level.round_number ) ) wait( 0.1 );
    players = get_players();
    while ( players.size < 1 )
    {
        wait( 0.1 );
        players = get_players();
    }
    if ( players.size != 1 )
    {
        IPrintLnBold( "Garden supports solo play." );
        return;
    }
    level.ng_owner = players[0];
    level.ng_owner thread player_loop();
    level.ng_owner thread carbine_peas();
    level.ng_owner thread held_plant_fire();
    level thread simulation();
    level thread cleanup();
    PrintLn( "NACHT_GARDEN_READY " + GetDvar( "mapname" ) );
    if ( GetDvar( "ng_audit" ) == "1" ) level thread audit();
}

new_hud()
{
    h = NewClientHudElem( self );
    h.horzAlign = "center";
    h.vertAlign = "middle";
    h.alignX = "center";
    h.alignY = "bottom";
    h.hidewheninmenu = true;
    h.alpha = 0;
    return h;
}

player_loop()
{
    self endon( "disconnect" );
    level endon( "intermission" );
    self.ng_text = self new_hud();
    self.ng_text.x = -184;
    self.ng_text.y = 64;
    self.ng_text.vertAlign = "top";
    self.ng_text.alignX = "center";
    self.ng_text.alignY = "top";
    self.ng_text.fontScale = 1.0;
    self.ng_text.color = (0.15,0.1,0.05);
    self.ng_text.sort = 4;
    self.ng_text.alpha = 1;
    self.ng_help = self new_hud();
    self.ng_help.x = -220;
    self.ng_help.y = 95;
    self.ng_help.vertAlign = "top";
    self.ng_help.alignX = "left";
    self.ng_help.alignY = "top";
    self.ng_help.fontScale = 1.0;
    self.ng_help.alpha = 1;
    self.ng_help SetText( "H: choose   J: hold plant   K: shovel   L: none" );
    self.ng_status = self new_hud();
    self.ng_status.x = -220;
    self.ng_status.y = 112;
    self.ng_status.vertAlign = "top";
    self.ng_status.alignX = "left";
    self.ng_status.alignY = "top";
    self.ng_status.fontScale = 1.0;
    self.ng_status.alpha = 1;
    self create_seedbank();
    self placement_status( "No plant selected. H chooses a seed packet." );
    self IPrintLnBold( "Nacht Garden: H chooses, J holds, fire plants, L puts away." );
    last_text = "";
    while ( true )
    {
        action = GetDvar( "ng_action" );
        if ( action != "" ) SetDvar( "ng_action", "" );
        alive = IsAlive( self ) && !self maps\_laststand::player_is_in_laststand();
        if ( alive )
        {
            if ( action == "next" )
            {
                if ( level.ng_selection < 0 ) level.ng_selection = 0;
                else level.ng_selection++;
                if ( level.ng_selection >= level.ng_types ) level.ng_selection = -1;
                if ( level.ng_selection >= 0 ) level.ng_page = Int( level.ng_selection / 6 );
                self selection_status();
            }
            if ( action == "page" )
            {
                level.ng_page = 1-level.ng_page;
                level.ng_selection = -1;
                self selection_status();
            }
            if ( action == "none" ) { level.ng_selection = -1; self selection_status(); }
            if ( action == "plant" ) self equip_plant();
            if ( action == "shovel" ) self shovel();
        }
        else if ( action != "" ) self placement_status( "You must be alive and standing to use plants." );
        text = "" + level.ng_sun;
        if ( text != last_text ) { self.ng_text SetText( text ); last_text = text; }
        self update_seedbank();
        spot = undefined;
        if ( alive && level.ng_selection >= 0 ) spot = self placement_spot();
        self preview( spot );
        for ( i = 0; i < level.ng_limit; i++ )
        {
            if ( IsDefined( level.ng_plants[i] ) ) level.ng_plants[i] face_player();
        }
        wait( 0.05 );
    }
}

selection_status()
{
    self put_plant_away();
    PlaySoundAtPosition( "ng_seedlift", self.origin );
    if ( level.ng_selection < 0 ) self placement_status( "No plant selected. H chooses a seed packet." );
    else self placement_status( level.ng_names[level.ng_selection] + " - " + level.ng_cost[level.ng_selection] + " sun. J holds it; fire places it." );
}

seed_hud( x, y )
{
    h = self new_hud();
    h.vertAlign = "top";
    h.alignX = "left";
    h.alignY = "top";
    h.x = x; h.y = y; h.alpha = 1;
    return h;
}

create_seedbank()
{
    self.ng_bank = self seed_hud( -223, 5 );
    self.ng_bank SetShader( "ng_seedbank", 446, 87 );
    self.ng_bank.sort = 0;
    self.ng_highlight = self seed_hud( -146, 12 );
    self.ng_highlight SetShader( "ng_packet_glow", 54, 74 );
    self.ng_highlight.sort = 1;
    self.ng_highlight.alpha = 0;
    self.ng_packets = [];
    for ( i = 0; i < 6; i++ )
    {
        h = self seed_hud( -145+i*52, 13 );
        h SetShader( level.ng_packet[i], 50, 70 );
        h.sort = 2;
        self.ng_packets[i] = h;
    }
    self.ng_drawn_page = -1;
}

update_seedbank()
{
    for ( i = 0; i < 6; i++ )
    {
        type = level.ng_page*6+i;
        h = self.ng_packets[i];
        h.alpha = 0;
        if ( type >= level.ng_types ) continue;
        h.alpha = 1;
        if ( self.ng_drawn_page != level.ng_page ) h SetShader( level.ng_packet[type],50,70 );
        h.color = (1,1,1);
        if ( level.ng_sun < level.ng_cost[type] ) h.color = (0.45,0.45,0.45);
        if ( GetTime() < level.ng_ready[type] ) h.color = (0.25,0.25,0.25);
        if ( type >= 8 && GetDvar( "mapname" ) != "nazi_zombie_sumpf" ) h.color = (0.25,0.25,0.25);
    }
    self.ng_drawn_page = level.ng_page;
    self.ng_highlight.alpha = 0;
    if ( level.ng_selection >= 0 )
    {
        self.ng_highlight.x = -147+(level.ng_selection-level.ng_page*6)*52;
        self.ng_highlight.alpha = 0.85;
    }
}

preview( spot )
{
    if ( !IsDefined( spot ) || level.ng_selection < 0 )
    {
        if ( IsDefined( self.ng_preview_entity ) ) self.ng_preview_entity Delete();
        self.ng_preview_entity = undefined;
        return;
    }
    type = level.ng_selection;
    if ( IsDefined( self.ng_preview_entity ) && self.ng_preview_type != type )
    { self.ng_preview_entity Delete(); self.ng_preview_entity = undefined; }
    if ( !IsDefined( self.ng_preview_entity ) )
    {
        self.ng_preview_entity = Spawn( "script_model", spot + (0,0,level.ng_anchor[type]) );
        self.ng_preview_entity SetModel( "tag_origin" );
        self.ng_preview_type = type;
        angles = VectorToAngles( self.origin-spot );
        self.ng_preview_entity.angles = (0,angles[1],0);
        PlayFXOnTag( level.ng_clips[level.ng_base[type]+"_preview"], self.ng_preview_entity, "tag_origin" );
    }
    self.ng_preview_entity.origin = spot + (0,0,level.ng_anchor[type]);
    angles = VectorToAngles( self.origin-spot );
    self.ng_preview_entity.angles = (0,angles[1],0);
}

placement_status( message )
{
    self.ng_status SetText( message );
    SetDvar( "ng_placement_status", message );
}

placement_spot()
{
    self.ng_spot_reason = "Ready to plant.";
    eye = self GetEye();
    direction = AnglesToForward( self GetPlayerAngles() );
    trace = BulletTrace( eye, eye + direction * 260, false, self );
    if ( trace["fraction"] == 1 )
    { self.ng_spot_reason = "Floor is out of reach. Aim farther down."; return undefined; }
    if ( trace["normal"][2] < 0.85 )
    { self.ng_spot_reason = "Aim at flat floor, away from walls and objects."; return undefined; }
    position = trace["position"];
    self.ng_spot_water = false;
    if ( GetDvar( "mapname" ) == "nazi_zombie_sumpf" && IsDefined( trace["surfacetype"] ) )
        self.ng_spot_water = trace["surfacetype"] == "water";
    if ( level.ng_selection >= 8 && !self.ng_spot_water )
    { self.ng_spot_reason = "This plant needs Shi No Numa water."; return undefined; }
    self.ng_pad = undefined;
    if ( self.ng_spot_water && level.ng_selection < 8 )
    {
        for ( i = 0; i < level.ng_limit; i++ )
        {
            pad = level.ng_plants[i];
            if ( !IsDefined( pad ) || pad.ng_type != 8 || IsDefined( pad.ng_child ) ) continue;
            if ( Distance( position,pad.origin ) < 32 ) { self.ng_pad = pad; break; }
        }
        if ( !IsDefined( self.ng_pad ) )
        { self.ng_spot_reason = "Place a Lily Pad first, then aim at its centre."; return undefined; }
        position = self.ng_pad.origin+(0,0,3);
    }
    if ( Distance( position, self.origin ) < 42 )
    { self.ng_spot_reason = "Too close to your feet. Aim a little farther away."; return undefined; }
    if ( Abs( position[2] - self.origin[2] ) > 60 )
    { self.ng_spot_reason = "Aim at floor on your level."; return undefined; }
    return position;
}

plant()
{
    if ( level.ng_selection < 0 ) { self selection_status(); return; }
    spot = self placement_spot();
    if ( !IsDefined( spot ) ) { self placement_status( self.ng_spot_reason ); return; }
    slot = -1;
    for ( i = 0; i < level.ng_limit; i++ )
    {
        if ( !IsDefined( level.ng_plants[i] ) ) slot = i;
        else if ( IsDefined( self.ng_pad ) && level.ng_plants[i] == self.ng_pad ) continue;
        else if ( Distance( level.ng_plants[i].origin, spot ) < 48 )
        { self placement_status( "Leave some space between plants." ); return; }
    }
    if ( slot < 0 ) { self placement_status( "18 plant limit reached. Shovel a plant first." ); return; }
    type = level.ng_selection;
    cost = level.ng_cost[type];
    if ( GetTime() < level.ng_ready[type] )
    {
        remaining = Int( (level.ng_ready[type]-GetTime())/1000 )+1;
        self placement_status( "Seed recharging: " + remaining + " seconds." ); return;
    }
    if ( level.ng_sun < cost ) { self placement_status( "Not enough sun." ); return; }
    self placement_status( "Checking planting spot..." );
    p = Spawn( "script_model", spot );
    p SetModel( "tag_origin" );
    if ( !p maps\_zombiemode_utility::in_playable_area() )
    { p Delete(); self placement_status( "Plant inside the playable area." ); return; }
    p.ng_type = type;
    p.ng_health = 300;
    if ( type == 8 ) p.ng_health = 180;
    if ( type == 2 ) p.ng_health = 1200;
    p.ng_next = GetTime() + 1000;
    if ( type == 1 ) p.ng_next = GetTime() + 6000;
    p.ng_state = "idle";
    p.ng_until = 0;
    p.ng_anim_until = 0;
    p.ng_blink_at = GetTime() + RandomIntRange( 4000, 9000 );
    p.ng_slot = slot;
    if ( type == 3 ) { p.ng_state = "fuse"; p.ng_until = GetTime()+900; }
    if ( type == 4 ) { p.ng_state = "unarmed"; p.ng_until = GetTime()+8000; }
    if ( IsDefined( self.ng_pad ) ) { p.ng_pad = self.ng_pad; self.ng_pad.ng_child = p; }
    level.ng_plants[slot] = p;
    level.ng_ready[type] = GetTime()+level.ng_cooldown[type];
    sound = "ng_plant";
    if ( RandomInt( 2 ) == 0 ) sound = "ng_plant2";
    if ( self.ng_spot_water ) sound = "ng_plant_water";
    PlaySoundAtPosition( sound,spot );
    p show_clip( level.ng_base[type]+"_idle" );
    level.ng_sun -= cost;
    self placement_status( "Planted " + level.ng_names[type] + "." );
    PrintLn( "NACHT_GARDEN_PLANTED " + type + " at " + spot );
}

shovel()
{
    eye = self GetEye();
    forward = AnglesToForward( self GetPlayerAngles() );
    best = -1;
    nearest = 280;
    for ( i = 0; i < level.ng_limit; i++ )
    {
        if ( !IsDefined( level.ng_plants[i] ) ) continue;
        p = level.ng_plants[i];
        to = p.origin + (0,0,24) - eye;
        dist = Length( to );
        if ( dist >= nearest || VectorDot( VectorNormalize( to ), forward ) < 0.93 ) continue;
        tr = BulletTrace( eye, p.origin + (0,0,24), false, self );
        if ( tr["fraction"] < 0.99 ) continue;
        best = i; nearest = dist;
    }
    if ( best < 0 ) { self IPrintLn( "Aim at a nearby plant to shovel it." ); return; }
    p = level.ng_plants[best];
    if ( p.ng_type == 8 && IsDefined( p.ng_child ) )
    { self placement_status( "Shovel the plant on this Lily Pad first." ); return; }
    PlaySoundAtPosition( "ng_shovel",p.origin );
    level.ng_sun += Int( level.ng_cost[p.ng_type] / 2 );
    level.ng_plants[best] = undefined;
    p remove_plant();
}

remove_plant()
{
    if ( IsDefined( self.ng_pad ) ) self.ng_pad.ng_child = undefined;
    if ( IsDefined( self.ng_child ) )
    {
        child = self.ng_child;
        child.ng_pad = undefined;
        level.ng_plants[child.ng_slot] = undefined;
        child remove_plant();
    }
    if ( IsDefined( self.ng_visual ) ) self.ng_visual Delete();
    self Delete();
}

face_player()
{
    if ( IsDefined( self.ng_visual ) && IsDefined( level.ng_owner ) )
    {
        angles = VectorToAngles( level.ng_owner.origin-self.origin );
        self.ng_visual.angles = (0,angles[1],0);
    }
}

show_clip( name )
{
    if ( IsDefined( self.ng_visual ) && self.ng_animation == name ) return;
    if ( IsDefined( self.ng_visual ) ) self.ng_visual Delete();
    self.ng_animation = name;
    self.ng_visual = Spawn( "script_model", self.origin + (0,0,level.ng_anchor[self.ng_type]) );
    self.ng_visual SetModel( "tag_origin" );
    self face_player();
    PlayFXOnTag( level.ng_clips[name], self.ng_visual, "tag_origin" );
}

idle_clip()
{
    if ( self.ng_type == 2 )
    {
        if ( self.ng_health <= 400 ) return "wallnut_crack2_idle";
        if ( self.ng_health <= 800 ) return "wallnut_crack1_idle";
    }
    if ( self.ng_type == 4 && self.ng_state == "armed" ) return "potatomine_armed";
    return level.ng_base[self.ng_type]+"_idle";
}

animate_once( name )
{
    self.ng_animation = "";
    self show_clip( name );
    self.ng_anim_until = GetTime()+level.ng_clip_msec[name];
}

nearest_zombie( radius )
{
    result = undefined;
    zombies = GetAiArray( "axis" );
    for ( i = 0; i < zombies.size; i++ )
    {
        z = zombies[i];
        if ( !IsAlive( z ) || Abs( z.origin[2]-self.origin[2] ) > 60 ) continue;
        d = Distance( self.origin,z.origin );
        if ( d >= radius ) continue;
        tr = BulletTrace( self.origin+(0,0,18),z.origin+(0,0,36),false,self );
        if ( tr["fraction"] < 0.99 ) continue;
        result = z; radius = d;
    }
    return result;
}

simulation()
{
    level endon( "intermission" );
    passive = GetTime() + 12000;
    while ( true )
    {
        now = GetTime();
        if ( now >= passive ) { level.ng_sun += 25; passive = now + 12000; }
        for ( i = 0; i < level.ng_limit; i++ )
        {
            if ( !IsDefined( level.ng_plants[i] ) ) continue;
            p = level.ng_plants[i];
            if ( p.ng_health <= 0 ) { level.ng_plants[i] = undefined; p remove_plant(); continue; }
            p tick_plant( now );
        }
        wait( 0.05 );
    }
}

tick_plant( now )
{
    if ( self.ng_type == 3 )
    {
        if ( now < self.ng_until ) return;
        if ( self.ng_state == "fuse" )
        {
            self.ng_state = "explode";
            self show_clip( "cherrybomb_explode" );
            self.ng_until = now + level.ng_clip_msec["cherrybomb_explode"];
            return;
        }
        self plant_explosion( 250, 1800, "powie" );
        return;
    }
    if ( self.ng_type == 4 )
    {
        if ( self.ng_state == "unarmed" && now >= self.ng_until )
        {
            PlaySoundAtPosition( "ng_dirt_rise",self.origin );
            self.ng_state = "rise";
            self show_clip( "potatomine_rise" );
            self.ng_until = now+level.ng_clip_msec["potatomine_rise"];
        }
        else if ( self.ng_state == "rise" && now >= self.ng_until )
        { self.ng_state = "armed"; self show_clip( "potatomine_armed" ); }
        if ( self.ng_state != "armed" ) return;
        victim = self nearest_zombie( 70 );
        if ( IsDefined( victim ) ) { self plant_explosion( 130,1800,"spudow" ); return; }
    }
    if ( self.ng_type == 0 || self.ng_type == 6 )
    {
        if ( self.ng_state == "shoot" )
        {
            if ( !self.ng_fired && now >= self.ng_fire_at )
            {
                self.ng_fired = true;
                if ( IsDefined( self.ng_target ) && IsAlive( self.ng_target ) )
                {
                    start = self.origin+(0,0,29);
                    level thread pea( start,VectorNormalize( self.ng_target.origin+(0,0,36)-start ) );
                    if ( self.ng_type == 6 ) self.ng_second_at = now+180;
                }
            }
            if ( self.ng_type == 6 && IsDefined( self.ng_second_at ) && now >= self.ng_second_at )
            {
                self.ng_second_at = undefined;
                if ( IsDefined( self.ng_target ) && IsAlive( self.ng_target ) )
                {
                    start = self.origin+(0,0,29);
                    level thread pea( start,VectorNormalize( self.ng_target.origin+(0,0,36)-start ) );
                }
            }
            if ( now < self.ng_until ) return;
            self.ng_state = "idle"; self.ng_next = now+450;
            self show_clip( self idle_clip() );
        }
        if ( now >= self.ng_next )
        {
            victim = self nearest_zombie( 850 );
            if ( IsDefined( victim ) )
            {
                self.ng_target = victim; self.ng_state = "shoot";
                self.ng_fired = false; self.ng_fire_at = now+550;
                self.ng_until = now+level.ng_clip_msec[level.ng_base[self.ng_type]+"_shoot"];
                self.ng_anim_until = 0;
                self show_clip( level.ng_base[self.ng_type]+"_shoot" );
                return;
            }
        }
    }
    if ( self.ng_type == 1 && now >= self.ng_next )
    {
        level.ng_sun += 25; self.ng_next = now+16000;
        PlaySoundAtPosition( "ng_points",self.origin );
        PlayFX( level.ng_clips["sun"],self.origin+(0,0,36) );
    }
    if ( self.ng_type == 5 )
    {
        if ( self.ng_state == "bite" )
        {
            if ( now >= self.ng_fire_at && !self.ng_fired )
            {
                self.ng_fired = true;
                victim = self.ng_target;
                if ( IsDefined( victim ) && IsAlive( victim ) && Distance( self.origin,victim.origin ) < 115 )
                {
                    tr = BulletTrace( self.origin+(0,0,20),victim.origin+(0,0,36),false,self );
                    if ( tr["fraction"] >= 0.99 )
                    {
                        // Only the eaten enemy receives damage. These are the
                        // original Nacht blood effects, with no blast damage.
                        blood = victim.origin+(0,0,42);
                        plant_blood_burst( blood );
                        victim DoDamage( victim.health+10000,blood,level.ng_owner );
                        victim thread hide_consumed();
                        PlaySoundAtPosition( "ng_bigchomp",self.origin );
                        self.ng_state = "chew"; self.ng_until = now+18000;
                        self show_clip( "chomper_chew" );
                        return;
                    }
                }
            }
            if ( now < self.ng_until ) return;
            self.ng_state = "idle"; self.ng_next = now+500;
            self show_clip( "chomper_idle" );
        }
        if ( self.ng_state == "chew" )
        {
            if ( now < self.ng_until ) return;
            PlaySoundAtPosition( "ng_gulp",self.origin );
            self.ng_state = "swallow";
            self.ng_until = now+level.ng_clip_msec["chomper_swallow"];
            self show_clip( "chomper_swallow" );
            return;
        }
        if ( self.ng_state == "swallow" )
        {
            if ( now < self.ng_until ) return;
            self.ng_state = "idle"; self.ng_next = now+500;
            self show_clip( "chomper_idle" );
        }
        if ( self.ng_state == "idle" && now >= self.ng_next )
        {
            victim = self nearest_zombie( 95 );
            if ( IsDefined( victim ) )
            {
                self.ng_state = "bite"; self.ng_target = victim;
                self.ng_fire_at = now+750; self.ng_fired = false;
                self.ng_until = now+level.ng_clip_msec["chomper_bite"];
                self.ng_anim_until = 0;
                self show_clip( "chomper_bite" );
                return;
            }
        }
    }
    if ( self.ng_type == 7 ) { self tick_squash( now ); return; }
    if ( self.ng_type == 9 ) { self tick_kelp( now ); return; }
    if ( self.ng_anim_until > 0 && now >= self.ng_anim_until )
    { self.ng_anim_until = 0; self show_clip( self idle_clip() ); }

}

walnut_variant()
{
    if ( self.ng_health <= 400 ) return "wallnut_crack2_";
    if ( self.ng_health <= 800 ) return "wallnut_crack1_";
    return "wallnut_";
}

hide_consumed()
{
    // Keep the original death script responsible for zombie counts and cleanup.
    wait( 0.1 );
    if ( IsDefined( self ) && !IsAlive( self ) ) self Hide();
}

// NG_ROSTER_SLAM_V1: original Nacht blood assets, shared by bite and slam.
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
    // 1800 base damage, then 65% of round health at high rounds: useful but
    // no longer a guaranteed whole-wave kill against late-round enemies.
    if ( IsDefined( level.zombie_health ) && level.zombie_health*0.65 > damage )
        damage = Int( level.zombie_health*0.65 );
    // Apply damage exclusively to the stock enemy AI array. Never call
    // RadiusDamage, spawn a grenade, or include players in blast candidates.
    zombies = GetAiArray( "axis" );
    for ( i = 0; i < zombies.size; i++ )
    {
        z = zombies[i];
        if ( !IsAlive( z ) || Distance( self.origin,z.origin ) > radius ) continue;
        if ( Abs( z.origin[2]-self.origin[2] ) > 90 ) continue;
        tr = BulletTrace( center,z.origin+(0,0,36),false,self );
        if ( tr["fraction"] >= 0.99 )
        {
            if ( bloody ) plant_blood_burst( z.origin+(0,0,42) );
            z DoDamage( damage,z.origin+(0,0,36),level.ng_owner );
        }
    }
}

plant_explosion( radius,damage,caption )
{
    center = self.origin+(0,0,20);
    if ( self.ng_type == 3 ) PlaySoundAtPosition( "ng_cherrybomb",self.origin );
    if ( self.ng_type == 4 ) PlaySoundAtPosition( "ng_potato_mine",self.origin );
    if ( self.ng_type == 7 ) PlaySoundAtPosition( "ng_floop",self.origin );
    self plant_area_damage( radius,damage,false );
    if ( caption != "" ) PlayFX( level.ng_clips[caption],center+(0,0,18) );
    if ( self.ng_type == 4 )
        level thread mine_remains( self.origin,level.ng_owner.origin );
    level.ng_plants[self.ng_slot] = undefined;
    self remove_plant();
}

mine_remains( origin,viewer )
{
    model = Spawn( "script_model",origin+(0,0,level.ng_anchor[4]) );
    model SetModel( "tag_origin" );
    angles = VectorToAngles( viewer-origin );
    model.angles = (0,angles[1],0);
    PlayFXOnTag( level.ng_clips["potatomine_mashed"],model,"tag_origin" );
    wait( 2 );
    if ( IsDefined( model ) ) model Delete();
}

carbine_peas()
{
    self endon( "disconnect" );
    level endon( "intermission" );
    while ( true )
    {
        self waittill( "weapon_fired" );
        weapon = self GetCurrentWeapon();
        if ( weapon != "m1carbine" && weapon != "m1carbine_bayonet" ) continue;
        if ( !IsAlive( self ) || self maps\_laststand::player_is_in_laststand() ) continue;
        forward = AnglesToForward( self GetPlayerAngles() );
        eye = self GetEye();
        muzzle = eye + forward * 30 + (0,0,-6);
        clear = BulletTrace( eye, muzzle, false, self );
        if ( clear["fraction"] < 1 ) continue;
        aim = eye + forward * 900;
        level thread pea( muzzle, VectorNormalize( aim - muzzle ) );
    }
}

pea( start, direction )
{
    // Both carbine and plants use this same fixed-speed world projectile.
    // Carbine peas supplement its existing shot, ammunition and recoil.
    level endon( "intermission" );
    sound = "ng_throw";
    if ( RandomInt( 2 ) == 0 ) sound = "ng_throw2";
    PlaySoundAtPosition( sound,start );
    position = start;
    travelled = 0;
    while ( travelled < 900 )
    {
        if ( !IsDefined( level.ng_owner ) || !IsAlive( level.ng_owner ) ) break;
        next = position + direction * 42;
        PlayFX( level.ng_pea_fx, position );
        tr = BulletTrace( position, next, true, level.ng_owner );
        if ( tr["fraction"] < 1 )
        {
            if ( IsDefined( tr["entity"] ) )
            {
                zombies = GetAiArray( "axis" );
                for ( i = 0; i < zombies.size; i++ )
                    if ( zombies[i] == tr["entity"] && IsAlive( zombies[i] ) )
                    {
                        damage = 40;
                        // Linear round-health contribution preserves a support
                        // role as CoD zombie health starts growing exponentially.
                        if ( IsDefined( level.zombie_health ) ) damage += Int( level.zombie_health*0.06 );
                        zombies[i] DoDamage( damage, tr["position"], level.ng_owner );
                        if ( GetTime() >= level.ng_last_hit_sound )
                        {
                            sounds = []; sounds[0] = "ng_splat"; sounds[1] = "ng_splat2"; sounds[2] = "ng_splat3";
                            PlaySoundAtPosition( sounds[RandomInt( 3 )],tr["position"] );
                            level.ng_last_hit_sound = GetTime()+100;
                        }
                        break;
                    }
            }
            break;
        }
        position = next; travelled += 42;
        wait( 0.05 );
    }
}

// Called only from stock zombie_follow_enemy, after entry/window navigation.
// Returning false immediately hands movement back to the original code.
garden_goal()
{
    if ( !IsDefined( level.ng_owner ) || !IsAlive( level.ng_owner ) ) return false;
    target = undefined; nearest = 150;
    for ( i = 0; i < level.ng_limit; i++ )
    {
        if ( !IsDefined( level.ng_plants[i] ) ) continue;
        p = level.ng_plants[i];
        if ( p.ng_type == 7 && p.ng_state != "idle" && p.ng_state != "look" ) continue;
        distance = Distance( self.origin, p.origin );
        radius = 90;
        if ( p.ng_type == 8 && IsDefined( p.ng_child ) ) continue;
        if ( p.ng_type == 2 ) radius = 150;
        if ( p.ng_health <= 0 || distance >= nearest || distance > radius ) continue;
        if ( Abs( self.origin[2] - p.origin[2] ) > 45 ) continue;
        tr = BulletTrace( self.origin+(0,0,30), p.origin+(0,0,30), false, self );
        if ( tr["fraction"] < 0.99 ) continue;
        target = p; nearest = distance;
    }
    if ( !IsDefined( target ) ) return false;
    if ( nearest > 42 ) { self SetGoalPos( target.origin ); return true; }
    self SetGoalPos( self.origin );
    if ( !IsDefined( self.ng_bite ) || GetTime() >= self.ng_bite )
    {
        target.ng_health -= 40;
        if ( !IsDefined( target.ng_bite_sound ) || GetTime() >= target.ng_bite_sound )
        {
            PlaySoundAtPosition( "ng_chomp",target.origin );
            target.ng_bite_sound = GetTime()+900;
        }
        if ( target.ng_type == 2 && target.ng_health > 0 )
        {
            // Change damaged artwork only when its health stage changes.
            // Restarting a blink on every bite interrupted the continuous loop.
            target show_clip( target idle_clip() );
        }
        self.ng_bite = GetTime() + 1000;
    }
    return true;
}

cleanup()
{
    level waittill( "intermission" );
    p = level.ng_owner;
    level.ng_owner = undefined;
    if ( IsDefined( p ) )
    {
        if ( IsDefined( p.ng_text ) ) p.ng_text Destroy();
        if ( IsDefined( p.ng_help ) ) p.ng_help Destroy();
        if ( IsDefined( p.ng_status ) ) p.ng_status Destroy();
        if ( IsDefined( p.ng_preview_entity ) ) p.ng_preview_entity Delete();
        if ( IsDefined( p.ng_bank ) ) p.ng_bank Destroy();
        if ( IsDefined( p.ng_highlight ) ) p.ng_highlight Destroy();
        for ( i = 0; i < 6; i++ )
        {
            if ( IsDefined( p.ng_packets[i] ) ) p.ng_packets[i] Destroy();
        }
    }
    for ( i = 0; i < level.ng_limit; i++ )
        if ( IsDefined( level.ng_plants[i] ) ) { level.ng_plants[i] remove_plant(); level.ng_plants[i] = undefined; }
}

// Original PvZ look/jump/land sprite poses travel on a native WaW mover.
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

tick_kelp( now )
{
    if ( self.ng_state == "idle" )
    {
        victim = self nearest_zombie( 95 );
        if ( !IsDefined( victim ) ) return;
        tr = BulletTrace( victim.origin+(0,0,40),victim.origin-(0,0,50),false,self );
        if ( !IsDefined( tr["surfacetype"] ) || tr["surfacetype"] != "water" ) return;
        self.ng_target = victim;
        self.ng_state = "grab";
        self.ng_until = now+level.ng_clip_msec["tanglekelp_grab"];
        self show_clip( "tanglekelp_grab" );
        return;
    }
    if ( now < self.ng_until ) return;
    victim = self.ng_target;
    if ( IsDefined( victim ) && IsAlive( victim ) && Distance( self.origin,victim.origin ) < 115 )
    {
        tr = BulletTrace( self.origin+(0,0,24),victim.origin+(0,0,36),false,self );
        if ( tr["fraction"] >= 0.99 )
        {
            PlaySoundAtPosition( "ng_zombiesplash",self.origin );
            victim DoDamage( victim.health+10000,victim.origin+(0,0,30),level.ng_owner );
            victim thread hide_consumed();
            level.ng_plants[self.ng_slot] = undefined;
            self remove_plant();
            return;
        }
    }
    self.ng_state = "idle";
    self show_clip( "tanglekelp_idle" );
}

// Opt-in local validation only. Normal launches never enter this routine.
audit()
{
    SetDvar( "ng_held_audit", "pending" );
    SetDvar( "ng_audit_result", "pending" );
    wait( 2 );
    PrintLn( "NG_AUDIT_STARTED" );
    if ( GetDvar( "mapname" ) == "nazi_zombie_sumpf" )
    {
        points = [];
        points[0] = (11426,130,-744);
        points[1] = (11224,-1222,-741);
        points[2] = (11688,-360,-740);
        for ( i = 0; i < points.size; i++ )
        {
            tr = BulletTrace( points[i]+(0,0,100),points[i]-(0,0,100),false,level.ng_owner );
            SetDvar( "ng_water_audit_"+i, "surface=" + tr["surfacetype"] + " hit=" + tr["position"] );
        }
    }
    player = level.ng_owner;
    level.ng_selection = 0;
    player equip_plant();
    wait( 2 );
    SetDvar( "ng_held_audit", player GetCurrentWeapon() );
    wait( 14 );
    player put_plant_away();
    level.ng_selection = -1;
    player selection_status();
    SetDvar( "ng_audit_result", "complete: "+GetDvar( "mapname" ) );
}

is_plant_weapon( weapon )
{
    for ( i = 0; i < level.ng_types; i++ )
        if ( weapon == level.ng_weapons[i] ) return true;
    return false;
}

equip_plant()
{
    if ( level.ng_selection < 0 ) { self selection_status(); return; }
    type = level.ng_selection;
    if ( level.ng_sun < level.ng_cost[type] ) { self placement_status( "Not enough sun." ); return; }
    if ( GetTime() < level.ng_ready[type] ) { self placement_status( "That seed is still recharging." ); return; }
    weapon = level.ng_weapons[type];
    current = self GetCurrentWeapon();
    if ( !is_plant_weapon( current ) ) self.ng_previous_weapon = current;
    self GiveWeapon( weapon );
    self SetWeaponAmmoClip( weapon,1 );
    self SetWeaponAmmoStock( weapon,0 );
    self SwitchToWeapon( weapon );
    self placement_status( "Aim at nearby floor and fire to set down " + level.ng_names[type] + ". L puts it away." );
}

put_plant_away()
{
    if ( IsAlive( self ) && !self maps\_laststand::player_is_in_laststand() && IsDefined( self.ng_previous_weapon ) && self HasWeapon( self.ng_previous_weapon ) )
        self SwitchToWeapon( self.ng_previous_weapon );
    self.ng_previous_weapon = undefined;
    for ( i = 0; i < level.ng_types; i++ )
        if ( self HasWeapon( level.ng_weapons[i] ) ) self TakeWeapon( level.ng_weapons[i] );
}

held_plant_fire()
{
    self endon( "disconnect" );
    level endon( "intermission" );
    while ( true )
    {
        self waittill( "grenade_fire",projectile,weapon );
        if ( !is_plant_weapon( weapon ) ) continue;
        // A custom Betty-based item drives the original hands animation.
        // Its grenade is harmless and is removed before it can land or arm.
        if ( IsDefined( projectile ) ) projectile Delete();
        if ( IsAlive( self ) && !self maps\_laststand::player_is_in_laststand() && level.ng_selection >= 0 && weapon == level.ng_weapons[level.ng_selection] )
            self plant();
        wait( 0.9 );
        if ( IsDefined( self ) ) self put_plant_away();
    }
}
