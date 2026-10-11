// Isolated A/B test. Both plants share health, attack logic and corrected shooting.
comparison_pair()
{
    selected = level.ng_selection;
    level.ng_selection = 0;
    centre = self placement_spot();
    level.ng_selection = selected;
    if ( !IsDefined( centre ) ) { self placement_status( self.ng_spot_reason ); return; }
    facing = VectorNormalize( (centre[0]-self.origin[0],centre[1]-self.origin[1],0) );
    right = (facing[1],0-facing[0],0);
    spots = [];
    candidates = [];
    slots = [];
    for ( i = 0; i < level.ng_limit; i++ )
        if ( !IsDefined( level.ng_plants[i] ) ) slots[slots.size] = i;
    if ( slots.size < 2 ) { self placement_status( "Shovel two plants to make room for the comparison." ); return; }
    valid = true;
    for ( i = 0; i < 2; i++ )
    {
        offset = -48;
        if ( i == 1 ) offset = 48;
        position = centre+right*offset;
        tr = BulletTrace( position+(0,0,30),position-(0,0,30),false,self );
        if ( tr["fraction"] == 1 || tr["normal"][2] < 0.85 ) valid = false;
        spots[i] = tr["position"];
        sight = BulletTrace( self GetEye(),spots[i]+(0,0,20),false,self );
        if ( sight["fraction"] < 0.99 || Distance( spots[i],self.origin ) < 42 ) valid = false;
        for ( j = 0; j < level.ng_limit; j++ )
            if ( IsDefined( level.ng_plants[j] ) && Distance( level.ng_plants[j].origin,spots[i] ) < 48 ) valid = false;
        p = Spawn( "script_model",spots[i] );
        p SetModel( "tag_origin" );
        candidates[i] = p;
        if ( !p maps\_zombiemode_utility::in_playable_area() ) valid = false;
    }
    if ( Abs( spots[0][2]-spots[1][2] ) > 4 ) valid = false;
    if ( !valid )
    {
        for ( i = 0; i < candidates.size; i++ ) candidates[i] Delete();
        self placement_status( "Aim at wide, clear, level floor for the comparison pair." );
        return;
    }
    for ( i = 0; i < 2; i++ )
    {
        p = candidates[i];
        p.ng_type = 0;
        p.ng_health = 300;
        p.ng_next = GetTime()+1000;
        p.ng_state = "idle";
        p.ng_until = 0;
        p.ng_anim_until = 0;
        p.ng_slot = slots[i];
        p.ng_original = i == 0;
        p.ng_comparison = true;
        p.ng_comparison_hold = true;
        level.ng_plants[slots[i]] = p;
        p show_clip( "peashooter_idle" );
    }
    if ( IsDefined( self.ng_comparison_caption ) ) self.ng_comparison_caption Destroy();
    self.ng_comparison_caption = self new_hud();
    self.ng_comparison_caption.y = -42;
    self.ng_comparison_caption.vertAlign = "bottom";
    self.ng_comparison_caption.fontScale = 1.2;
    self.ng_comparison_caption.alpha = 1;
    self.ng_comparison_caption SetText( "Placement view: LEFT Original 12 | RIGHT AMD 60 - N: toggle shooting" );
    self placement_status( "Pair placed free for testing. Idle first; N enables both to shoot." );
    PrintLn( "AMD_COMPARISON_PAIR_READY" );
}

comparison_toggle()
{
    for ( i = 0; i < level.ng_limit; i++ )
    {
        p = level.ng_plants[i];
        if ( !IsDefined( p ) || !IsDefined( p.ng_comparison ) ) continue;
        p.ng_comparison_hold = !p.ng_comparison_hold;
        p.ng_state = "idle";
        p.ng_next = GetTime()+1000;
        p.ng_anim_until = 0;
        p.ng_animation = "";
        p show_clip( "peashooter_idle" );
    }
    self placement_status( "Comparison shooting toggled for both plants." );
}
