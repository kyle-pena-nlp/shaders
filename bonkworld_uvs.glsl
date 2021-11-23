
// { "uv": ("3", 0.25),  "image_idxs": ("4", 0.25), "lighting": ("5", 0.25), "normals": ("1", 0.25) }
#define RENDER_MODE 4

// 0 - unnormalized UV
// 1 - normal
// 2 - grid
// 3 - UV
// 4 - image idxs (when RG is divided by blue channel)
// 5 - lighting

#define PI 3.14159
#define AA 1
#define SPHERE_RADIUS 100.
#define START_DIST 4.
#define END_DIST 100.
#define LOOP_TIME 15.

const float GRID_MOD = 1. / 40.;
const vec3 SUNLIGHT_DIR = vec3(0.4, 0.7, 0.1);
const float WORLD_ROTATE_RATE = 2.*PI*(1./LOOP_TIME) / 2.;

struct Params {
    vec2  fragCoord;
    vec2  iResolution;               
	float time;       
};

// how to cast into the scene --- castRay returns a vec4 of <d, obj_id, uv>
struct Query {
    vec3 ro;
    vec3 rd;
};



struct QueryResult {
    float d;
    float obj_id;
    vec3 uvw;
    //vec3 norm;
    
};

// for camera and box
struct Transform {
    mat4 txi;
    mat4 txx;
};


// Compute camera-to-world transformation.
mat3 setCamera( in vec3 ro, in vec3 ta, float cr )
{
	vec3 cw = normalize(ta - ro);
	vec3 cp = vec3(sin(cr), cos(cr),0.0);
	vec3 cu = normalize( cross(cw,cp) );
	vec3 cv = normalize( cross(cu,cw) );
    return mat3( cu, cv, cw );
}

// vec3(distance, material uv)
QueryResult sdSphere( vec3 p, vec3 center, float radius)
{
    vec3  p_ = (p  - center);
    float p_radius = length(p_);
    float d = p_radius - radius;
    vec3 p_normed = normalize(p);
    
    float theta = PI + atan(pow(p_normed.x*p_normed.x + p_normed.z*p_normed.z, 0.5), p_normed.y);
    float phi   = PI + atan(p_normed.x, p_normed.z);

    vec3 uvw = vec3(theta, phi, d);

	return QueryResult(d, 1., uvw); // vec4(p.y, p.xyz) maybe?
}


Query getQuery(in Params params)
{
    float time = mod(params.time, LOOP_TIME);
    float yt = 0.5 * smoothstep(0.65 * LOOP_TIME, 0.85 * LOOP_TIME, time);

    vec2 p = (-params.iResolution.xy + 2.0*params.fragCoord)/params.iResolution.y;

    // todo: move camera on right click, interact on left click: + CAMERA_MOUSE * 2. * mo.y
    vec3 ro = vec3( 0.0, 0.0, 1.0 );
    vec3 ta = vec3( 0.0, yt, 0.0 );
    // camera-to-world transformation
    mat3 ca = setCamera( ro, ta, 0.0 );
    // ray direction
    vec3 rd = ca * normalize( vec3(p.xy,2.0) );
    
    return Query(ro, rd);
}


mat4 translate( float x, float y, float z )
{
    return mat4( 1.0, 0.0, 0.0, 0.0,
				 0.0, 1.0, 0.0, 0.0,
				 0.0, 0.0, 1.0, 0.0,
				 x,   y,   z,   1.0 );
}

// matrix math helper, ty inigo quilez
mat4 rotationAxisAngle( vec3 v, float angle )
{
    float s = sin( angle );
    float c = cos( angle );
    float ic = 1.0 - c;

    return mat4( v.x*v.x*ic + c,     v.y*v.x*ic - s*v.z, v.z*v.x*ic + s*v.y, 0.0,
                 v.x*v.y*ic + s*v.z, v.y*v.y*ic + c,     v.z*v.y*ic - s*v.x, 0.0,
                 v.x*v.z*ic - s*v.y, v.y*v.z*ic + s*v.x, v.z*v.z*ic + c,     0.0,
			     0.0,                0.0,                0.0,                1.0 );
}


//const float END_DIST = -1.;
//const float START_DIST = -0.1 + SPHERE_RADIUS;

Transform getBonkWorldTransform(Params params) {

    float time = mod(params.time, LOOP_TIME);

    float tz = smoothstep(0.1 * LOOP_TIME, 0.6 * LOOP_TIME, time);
    float z = (START_DIST + SPHERE_RADIUS) + tz*(END_DIST - START_DIST);
    vec3 boxPos = vec3(0.0, 0.0, -1. * z);
    mat4 rot1 = rotationAxisAngle( normalize(vec3(1.0,0.0,0.0)), 0.  );
    mat4 rot2 = rotationAxisAngle( normalize(vec3(0.0,1.0,0.0)), WORLD_ROTATE_RATE*time);
    mat4 rot3 = rotationAxisAngle( normalize(vec3(0.0,0.0,1.0)), 0. );
	mat4 tra1 = translate(boxPos.x, boxPos.y, boxPos.z);
    mat4 tra2 = translate(0., 0., 0.);
	mat4 txi =  tra1 * rot3 * rot2 * rot1 * tra2;// order deliberate.
	mat4 txx = inverse( txi );
    return Transform(txi, txx);
}


QueryResult map( in vec3 pos, in Params params)
{
    
    // plane
    Transform boxTransform = getBonkWorldTransform(params);
    vec3 bonkWorldPos = (boxTransform.txx * vec4(pos,1.)).xyz;
    QueryResult scene = sdSphere(bonkWorldPos, vec3(0.), SPHERE_RADIUS);
    
    return scene;
}

// Cast a ray from origin ro in direction rd until it hits an object.
// Return (t,m,a) where t is distance traveled along the ray, and m
// is the material of the object hit, and a is an auxilliary material channel
QueryResult castRay( in Query query, in Params params )
{
    float tmin = 0.1;
    float tmax = 200.0;

    vec3 rd = query.rd;
    vec3 ro = query.ro;
   
    // bounding volume
    //float tp1 = (-0.1-ro.y)/rd.y; if( tp1>0.0 ) tmax = min( tmax, tp1 );
    //float tp2 = (1.6-ro.y)/rd.y; if( tp2>0.0 ) { if( ro.y>1.6 ) tmin = max( tmin, tp2 );
    //                                             else           tmax = min( tmax, tp2 ); }
    
    float t = tmin;


    float obj_id = -1.0;
    vec3  uvw    = vec3(0.);

    for( int i=0; i<64; i++ )
    {
	    float precis = 0.000000001*t;
	    QueryResult res = map( ro+rd*t, params);
        if( res.d<precis || t>tmax ) break;
        t += 0.9*res.d;
	    obj_id = res.obj_id;
        uvw = res.uvw;
    }

    if( t>tmax )
    {
        obj_id=-1.;
        uvw = vec3(0.,rd.y, 0.);
    }
    return QueryResult( t, obj_id, uvw);
}

float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax, in Params params)
{
	float res = 1.0;
    float t = mint;
    for( int i=0; i<16; i++ )
    {
		float h = map( ro + rd*t, params).d;
        res = min( res, 6.0*h/t );
        t += clamp( h, 0.02, 0.10 );
        if( h<0.001 || t>tmax ) break;
    }
    return clamp( res, 0.0, 1.0 );
}

vec3 calcNormal( in vec3 pos, in Params params )
{
    // epsilon = a small number
    vec2 e = vec2(1.0,-1.0)*0.5773*0.0005;
    
    return normalize( e.xyy*map( pos + e.xyy, params ).d + 
					  e.yyx*map( pos + e.yyx, params ).d + 
					  e.yxy*map( pos + e.yxy, params ).d + 
					  e.xxx*map( pos + e.xxx, params ).d );

}

// compute ambient occlusion value at given position/normal
float calcAO( in vec3 pos, in vec3 nor, in Params params )
{
	float occ = 0.0;
    float sca = 1.0;
    for( int i=0; i<5; i++ )
    {
        float hr = 0.01 + 0.12*float(i)/4.0;
        vec3 aopos =  nor * hr + pos;
        float dd = map( aopos, params).d;
        occ += -(dd-hr)*sca;
        sca *= 0.95;
    }
    return clamp( 1.0 - 3.0*occ, 0.0, 1.0 );    
}

// Render by fetching from the scene buffer and interpreting it to get diffuse
// TODO: Then, add in shadows, AO, etc.
vec3 render2(in vec2 fragCoord)
{

    Params params = Params(  fragCoord, iResolution.xy, iTime);
    Query query = getQuery(params);
    QueryResult scene = castRay( query, params);

    // Get the scene info from the scene buffer
    //vec4 scene = texelFetch(iChannel1, ivec2(fragCoord), 0);
    
    // alias some stuff from the scene buffer
    float d      = scene.d;
    float obj_id = scene.obj_id;
    
    // form query based on current camera position, combine with depth to get scene position
    vec3 rd = query.rd;
    vec3 ro = query.ro;
    vec3 pos = d * rd + ro;
    
    /*vec3 mouseWorldPos     = getMouseWorldPos();
    if (length(pos - mouseWorldPos) < 0.25)
    {
        return vec3(1.);
    }*/

    vec2 uv = scene.uvw.xy;
    vec2 normalized_UV = uv/(2.*PI);



    float spec = 1.;
    
    if (obj_id < 0.) {
        return vec3(0.);
    }
    
    // sanity check
    if ((normalized_UV.x < 0.) || (normalized_UV.y < 0.)) {
        return vec3(1.);
    }
    
    // sanity check
    if ((normalized_UV.y > 1.) || (normalized_UV.y > 1.)) {
        return vec3(1.);
    }

    if (RENDER_MODE == 0) {
        return vec3(normalized_UV, 0.);
    }
    else if (RENDER_MODE == 1) {
        return calcNormal(pos, params);
    }
    else if (RENDER_MODE == 2) {
        vec2 modded = mod(normalized_UV + GRID_MOD/2.,GRID_MOD);
        float vec_min = min(modded.x, modded.y);
        float grid = vec_min < (GRID_MOD / 50.) ? 1. : 0.;
        return vec3(grid);
    }
    else if (RENDER_MODE == 3) {
        vec2 image_frac_coords = mod((normalized_UV + GRID_MOD/2.) * 1./GRID_MOD, 1.0);
        return vec3(image_frac_coords, 0.0);
    }
    else if (RENDER_MODE == 4) {
        vec2 image_idx = floor((normalized_UV + (GRID_MOD/2.) ) / GRID_MOD) * GRID_MOD;
        return vec3(image_idx, GRID_MOD);

    }
    else if (RENDER_MODE == 5) {
        vec3 col = vec3(1.);
        vec3 nor = calcNormal( pos, params);
        vec3 ref = reflect( rd, nor ); // reflected ray

        // lighting        
        float occ = calcAO( pos, nor, params); // ambient occlusion
		vec3  lig = normalize( SUNLIGHT_DIR ); // sunlight
		float amb = clamp( 0.5+0.5*nor.y, 0.0, 1.0 ); // ambient light
        float dif = clamp( dot( nor, lig ), 0.0, 1.0 ); // diffuse reflection from sunlight
        // backlight
        float bac = clamp( dot( nor, normalize(vec3(-lig.x,0.0,-lig.z))), 0.0, 1.0 )*clamp( 1.0-pos.y,0.0,1.0);
        float dom = smoothstep( -0.1, 0.1, ref.y ); // dome light
        float fre = pow( clamp(1.0+dot(nor,rd),0.0,1.0), 2.0 ); // fresnel
		float spe = pow(clamp( dot( ref, lig ), 0.0, 1.0 ),16.0); // specular reflection
        
        dif *= softshadow( pos, lig, 0.02, 2.5, params);
        dom *= softshadow( pos, ref, 0.02, 2.5, params);

		vec3 lin = vec3(0.0);
        lin += (1.30)*dif*vec3(0.75,0.75,0.75);
		lin += (2.00 + spec)*spe*vec3(0.80,0.80,0.80)*dif;
        lin += 0.40*amb*vec3(0.60,0.60,0.60)*occ;
        //lin += 0.50*dom*vec3(0.60,0.60,0.60)*occ;
        //lin += 0.50*bac*vec3(0.25,0.25,0.25)*occ;
        lin += 0.25*fre*vec3(1.00,1.00,1.00)*occ;
		col = col*lin;  

        return col;      
    }

    return vec3(1.);
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{

    vec3 tot = vec3(0.0);
#if AA>1
    for( int m=ZERO; m<AA; m++ )
    for( int n=ZERO; n<AA; n++ )
    {
        // pixel coordinates
        vec2 o = vec2(float(m),float(n)) / float(AA) - 0.5;
        //vec2 p = (2.0*(fragCoord+o)-iResolution.xy)/iResolution.y;
        vec3 col = render2(fragCoord + o);
#else    
        //vec2 p = (2.0*fragCoord-iResolution.xy)/iResolution.y;
        vec3 col = render2(fragCoord);
#endif

    
    
    tot += col;
    
#if AA>1
    }
    tot /= float(AA*AA);
#endif

    fragColor = vec4(tot, 1.);
}