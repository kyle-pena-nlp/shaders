


vec2 get_mouse_perturbation(in vec2 fragCoord) {
    // read mouse variables
    bool draw      = texelFetch(iChannel1, DRAW_ADDR, 0).x > 0.;
    vec2 m2 = texelFetch(iChannel1, M2_POS_ADDR, 0).xy;
    vec2 m1 = texelFetch(iChannel1, M1_POS_ADDR, 0).xy;
    vec2 m0 = texelFetch(iChannel1, M0_POS_ADDR, 0).xy;

    return get_mouse_perturbation_calcuation(fragCoord, draw, m2, m1, m0);
}

float getDivergence(in vec2 fragCoord) {
    
    // sample the velocities around this point
    vec2 va = texelFetch(iChannel0, (ivec2(fragCoord) + ivec2(-1,-1)) % ivec2(iResolution.xy), 0).xy;
    vec2 vb = texelFetch(iChannel0, (ivec2(fragCoord) + ivec2(-1, 0)) % ivec2(iResolution.xy), 0).xy;
    vec2 vc = texelFetch(iChannel0, (ivec2(fragCoord) + ivec2(-1, 1)) % ivec2(iResolution.xy), 0).xy;
    vec2 vd = texelFetch(iChannel0, (ivec2(fragCoord) + ivec2( 0,-1)) % ivec2(iResolution.xy), 0).xy;
    vec2 ve = texelFetch(iChannel0, (ivec2(fragCoord) + ivec2( 0, 0)) % ivec2(iResolution.xy), 0).xy;
    vec2 vf = texelFetch(iChannel0, (ivec2(fragCoord) + ivec2( 0, 1)) % ivec2(iResolution.xy), 0).xy;
    vec2 vg = texelFetch(iChannel0, (ivec2(fragCoord) + ivec2( 1,-1)) % ivec2(iResolution.xy), 0).xy;
    vec2 vh = texelFetch(iChannel0, (ivec2(fragCoord) + ivec2( 1, 0)) % ivec2(iResolution.xy), 0).xy;
    vec2 vi = texelFetch(iChannel0, (ivec2(fragCoord) + ivec2( 1, 1)) % ivec2(iResolution.xy), 0).xy;

    return divergence_calculation(va,vb,vc,vd,ve,vf,vg,vh,vi);
    
    //return (va+vb+vc+vd+ve+vf+vg+vh+vi)/9.;
}

vec2 get_v(in vec2 fragCoord) {
    return texture(iChannel0, fragCoord / iResolution.xy).xy;
}

float shade(vec2 fragCoord) {
    float a = length(get_v(fragCoord+ vec2(1,0))); //voronoi_f1_colors( 10.* (fragCoord + vec2(0,1)) / iResolution.xy, 1.0, 2.0, 3.14159/4.).w;
    float b = length(get_v(fragCoord + vec2(-1,0)));//voronoi_f1_colors( 10.* (fragCoord + vec2(0,-1)) / iResolution.xy, 1.0, 2.0, 3.14159/4.).w;
    float c = length(get_v(fragCoord + vec2(0,1)));//voronoi_f1_colors( 10.* (fragCoord + vec2(1,0)) / iResolution.xy, 1.0, 2.0, 3.14159/4.).w;
    float d = length(get_v(fragCoord + vec2(0,-1)));//voronoi_f1_colors( 10.* (fragCoord + vec2(-1,0)) / iResolution.xy, 1.0, 2.0, 3.14159/4.).w;
    vec2 grad = normalize(vec2((a-b)/2., (c-d)/2.));
    vec2 light = vec2(cos(iTime),sin(iTime));
    return 0.5 + 0.5 *dot(grad,light);
    //return 5.*a;
}


// from https://www.shadertoy.com/view/MsjXRt
// todo: my own implementation
vec3 HueShift (in vec3 Color, in float Shift)
{
    vec3 P = vec3(0.55735)*dot(vec3(0.55735),Color);
    
    vec3 U = Color-P;
    
    vec3 V = cross(vec3(0.55735),U);    

    Color = U*cos(Shift*6.2832) + V*sin(Shift*6.2832) + P;
    
    return Color;
}


void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord / iResolution.xy;

    // sample flow map
    vec2 flow = texture(iChannel0, (fragCoord)/iResolution.xy).xy;
    
    // get some vector quantities
    float d = getDivergence(fragCoord);
    float divergence = clamp(-d, 0.,1.);
    float convergence = clamp(d, 0., 1.);

    // use the flowmap to offset sampling into the previous frame
    vec4 prev = texture(iChannel2, vec2(fragCoord - flow) / iResolution.xy);
    
    // TRAITS: 0.99, 0.999
    prev*=0.99;
    
    //vec4 colors =  voronoi_f1_colors( VORONOI_UV_SCALE * fragCoord / iResolution.xy, VORONOI_RANDOMNESS, VORONOI_EXPONENT, VORONOI_ANGLE);
    
    // TRAIT: 1.- is a trait
    vec4 colors = texture(iChannel3, fragCoord / iResolution.xy);

    vec3 result = clamp(0.15*divergence * colors.xyz + (1.-0.15*divergence) * prev.xyz, 0., 1.);
    
    float mouse_movement = length(get_mouse_perturbation(fragCoord));
    
    //result = HueShift(result, length(result)*30.);
    
    result = (1.+0.01*length(flow))*HueShift(clamp(result,0.,1.), 0.005*length(flow));

    //vec3 result = shade(fragCoord) * mix(prev.xyz, colors.xyz, divergence);
    fragColor = vec4(result,colors.w);// vec4(divergence,divergence,divergence,1.);
    //}
}