/*
Flow Map
*/



const float fade = 0.9;
const float eps = 1e-3;



vec2 sign_preserving_max(vec2 a, vec2 b) {

    float x1 = a.x;
    float y1 = a.y;
    float x2 = b.x;
    float y2 = b.y;
    
    float x = max(abs(x1),abs(x2));
    x *= (x == abs(x1)) ? sign(x1) : sign(x2);
    
    float y = max(abs(y1),abs(y2));
    y *= (y == abs(y1)) ? sign(y1) : sign(y2);
    
    return vec2(x,y);
}

vec2 get_mouse_perturbation(in vec2 fragCoord) {
    // read mouse variables
    bool draw      = texelFetch(iChannel1, DRAW_ADDR, 0).x > 0.;
    vec2 m2 = texelFetch(iChannel1, M2_POS_ADDR, 0).xy;
    vec2 m1 = texelFetch(iChannel1, M1_POS_ADDR, 0).xy;
    vec2 m0 = texelFetch(iChannel1, M0_POS_ADDR, 0).xy;

    return get_mouse_perturbation_calcuation(fragCoord, draw, m2, m1, m0);
}

float weight_closeness(vec2 x) {
    return (1. + eps) / (eps+ length(x) );
}

vec2 getAdvectedV(in vec2 fragCoord) {
    
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

    // where the neighboring grid positions end up after the timestep
    vec2 pa = (va + vec2(-1.,-1.));
    vec2 pb = (vb + vec2(-1,  0.));
    vec2 pc = (vc + vec2(-1., 1.));
    vec2 pd = (vd + vec2( 0.,-1.));
    vec2 pe = (ve + vec2( 0., 0.));
    vec2 pf = (vf + vec2( 0., 1.));
    vec2 pg = (vg + vec2( 1.,-1.));
    vec2 ph = (vh + vec2( 1., 0.));
    vec2 pi = (vi + vec2( 1., 1.));
    
    /*
    float wa = max(eps,1.-length(pa));
    float wb = max(eps,1.-length(pb));
    float wc = max(eps,1.-length(pc));
    float wd = max(eps,1.-length(pd));
    float we = max(eps,1.-length(pe));
    float wf = max(eps,1.-length(pf));
    float wg = max(eps,1.-length(pg));
    float wh = max(eps,1.-length(ph));
    float wi = max(eps,1.-length(pi));
    */
    float wa = weight_closeness(pa);
    float wb = weight_closeness(pb);
    float wc = weight_closeness(pc);
    float wd = weight_closeness(pd);
    float we = weight_closeness(pe);
    float wf = weight_closeness(pf);
    float wg = weight_closeness(pg);
    float wh = weight_closeness(ph);
    float wi = weight_closeness(pi);
    
    
    float denom = max(eps,wa+wb+wc+wd+we+wf+wg+wh+wi);
    return ((wa*va + wb*vb + wc*vc + wd*vd + we*ve + wf*vf + wg*vg + wh*vh + wi*vi))/ denom;
    
    //return (va+vb+vc+vd+ve+vf+vg+vh+vi)/9.;
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

vec2 bound(vec2 x) {
    return length(x) > 1. ? normalize(x) : x;
}

vec2 get_random_v(in vec2 fragCoord) {
    return voronoi_f1_colors( fragCoord, VORONOI_RANDOMNESS, VORONOI_EXPONENT, VORONOI_ANGLE).xy - 0.5;
}

vec2 camGradient(in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 e = vec2(0.5/iResolution.x, 0.);
    #if SOURCE == 0
    vec2 grad = vec2(length(texture(iChannel3, uv + e.xy).xyz) - length(texture(iChannel3, uv - e.xy).xyz),
                length(texture(iChannel3, uv + e.yx).xyz) - length(texture(iChannel3, uv - e.yx).xyz));
    #else
    vec2 grad = vec2(length(voronoi_f1_colors( uv + e.xy, VORONOI_RANDOMNESS, VORONOI_EXPONENT, VORONOI_ANGLE ).xyz) -
    length(voronoi_f1_colors( uv - e.xy, VORONOI_RANDOMNESS, VORONOI_EXPONENT, VORONOI_ANGLE ).xyz),
    length(voronoi_f1_colors( uv + e.yx, VORONOI_RANDOMNESS, VORONOI_EXPONENT, VORONOI_ANGLE ).xyz) -
    length(voronoi_f1_colors( uv - e.yx, VORONOI_RANDOMNESS, VORONOI_EXPONENT, VORONOI_ANGLE ).xyz));
    //vec2 grad = vec2(length(texture(iChannel3, uv + e.xy).xyz) - length(texture(iChannel3, uv - e.xy).xyz),
    //            length(texture(iChannel3, uv + e.yx).xyz) - length(texture(iChannel3, uv - e.yx).xyz));
    #endif
    return grad;
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 random_v = get_random_v(VORONOI_UV_SCALE*fragCoord/iResolution.xy); //texture(iChannel2,0.1*fragCoord/iResolution.xy).xy-vec2(0.5);

    if (1 == 0) {
        fragColor = vec4(random_v,1.,1.);
    }
    else {
    
    // TRAIT: -1. * 
    vec2 cam_grad = camGradient(fragCoord);

    // advection step
    vec2 v = getAdvectedV(fragCoord);
    
    float d = getDivergence(fragCoord);
    
    //v = v * (1. + length(cam_grad));

    vec2 perturb = clamp(get_mouse_perturbation(fragCoord), -1.,1.);
    
    // TRAIT: oscillate?
    //v = v + perturb + clamp(sin(2.*iTime),0.,1.) * cam_grad;
    
    v = v + perturb + 0.5 * cam_grad;
    
    v = bound(v);
    
    fragColor = vec4(v,0.,1.);
    }
}