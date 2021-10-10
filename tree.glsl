const int AA = 2;

const float pi = 3.14159;

const mat3 noise_3d_rotator = mat3( 0.00,  0.80,  0.60,
                    -0.80,  0.36, -0.48,
                    -0.60, -0.48,  0.64 );
                    
mat2 noise2d_rotator = mat2(-0.8, 0.6, 0.6, 0.8);

float smoothlocal(float t, float I, float II, float eps) {
    return smoothstep(I-eps, I+eps, t) * (1.-smoothstep(II-eps,II+eps, t));
}



const vec3 SKY_BASE_COLOR = vec3(0.7, 0.9, 1.0);

const float PI = 3.14159;

// environment
const vec3 SUNLIGHT_DIR = vec3(0.4, 0.7, 0.1);

const vec3 X_AXIS = vec3(1.,0.,0.);
const vec3 Y_AXIS = vec3(0.,1.,0.);
const vec3 Z_AXIS = vec3(0.,0.,1.);

// Procedural 3d noise from Inigo Quilez at https://www.shadertoy.com/view/4sfGzS
float hash(vec3 p)  // replace this by something better
{
    p  = fract( p*0.3183099+.1 );
	p *= 17.0;
    return fract( p.x*p.y*p.z*(p.x+p.y+p.z) );
}

// object ID definitions (DO NOT MODIFY)
const float SKY   = -1.;
const float PLANE = 1.;
const float TREE = 2.;

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

// what gets returns from a uv/material query
struct Material {
   vec3  col;
   vec3  nor;
   float spec;
};

struct QueryResult {
    float d;
    float obj_id;
    vec3 uvw;
    //vec3 norm;
    
};




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


mat4 identityTransform() {
    mat4 eye = mat4( 1.0, 0.0, 0.0, 0.0,
				 0.0, 1.0, 0.0, 0.0,
				 0.0, 0.0, 1.0, 0.0,
				 0.0, 0.0, 0.0, 1.0 );
                 
    return eye;
}

// matrix math helper. ty inigo quilez
mat4 translate( mat4 transform, vec3 t )
{
    mat4 forwards = mat4( 1.0, 0.0, 0.0, 0.0,
				 0.0, 1.0, 0.0, 0.0,
				 0.0, 0.0, 1.0, 0.0,
				 t.x, t.y, t.z,   1.0 );
   
   return forwards * transform;
}

mat4 rotate( mat4 transform, vec3 v, float angle ) {
    mat4 forwards = rotationAxisAngle(v, angle);
    
    return forwards * transform;
}

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
QueryResult sdPlane( vec3 p, float time )
{    
    float d  = p.y;
    vec3 uvw  = p.xzy;

	return QueryResult(d, PLANE, uvw); // vec4(p.y, p.xyz) maybe?
}



QueryResult sdCapsule( vec3 p, vec3 a, vec3 b, float r)
{

    vec3 pa = p - a, ba = b - a;
    float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 );
    float d = length( pa - ba*h ) - r;
    vec3 uvw = vec3(0.);
    return QueryResult(d, TREE, uvw);
}

// x, m, uv
QueryResult opS2(in QueryResult d1, in QueryResult d2 )
{
    float a = (d1.d > -d2.d) ? 1. : 0.;
    float b = 1. - a;

    float d      = a * d1.d  + b * -d2.d;
    float obj_id = a * d1.obj_id  + b * d2.obj_id;
    vec3 uvw     = a * d1.uvw + b * d2.uvw;

    return QueryResult(d, obj_id, uvw);
    //return (d1.d > -d2.d) ? d1 : Casting(-d2.d, d2.mat, d2.mat_aux);
    //max(d1.x, -d2.x)
}

// union primitives 1 and 2
// d1 is a vec2 where .x is the distance, and .y is the color/material code.
QueryResult opU2(in QueryResult d1, in QueryResult d2 )
{
    float a = (d1.d < d2.d) ? 1.0 : 0.0;
    float b = 1. - a;

    float d      = a * d1.d  + b * d2.d;
    float obj_id = a * d1.obj_id  + b * d2.obj_id;
    vec3 uvw     = a * d1.uvw + b * d2.uvw;

	//return (d1.d<d2.d) ? d1 : d2;
    return QueryResult(d, obj_id, uvw);
}

struct Segment {
    vec3 pos;
    mat4 orientation;
    float length;
    float width;
};

struct Branch {
    Segment A;
    Segment B;
    Segment C;
    Segment D;
};

vec3 endOfSegment(Segment segment) {
    return segment.pos + (segment.orientation * vec4(0.,segment.length,0.,0.)).xyz;
}

QueryResult sdSegment(vec3 p, Segment segment) {
    return sdCapsule(p, segment.pos, endOfSegment(segment), segment.width);
}

QueryResult sdBranch(vec3 p, in Branch branch)
{
    QueryResult a = sdSegment(p, branch.A);
    QueryResult b = sdSegment(p, branch.B);
    QueryResult c = sdSegment(p, branch.C);
    QueryResult d = sdSegment(p, branch.D);
    return opU2(opU2(a, b), opU2(c, d));
}

mat4 perturb(mat4 transform, vec3 seed, float scale) {
    float randAngle1 = scale * 2. * PI * (hash((1.*seed))-0.5);
    float randAngle2 = scale * 2. * PI * (hash((2.*seed))-0.5);
    float randAngle3 = scale * 2. * PI * (hash((3.*seed))-0.5);
    return rotate(rotate(rotate(transform, X_AXIS, randAngle1), Y_AXIS, randAngle2), Z_AXIS, randAngle3);
}

float grow(float t, float startT, float endT) {
    return clamp(t - startT, 0., endT - startT) / (endT-startT);
}

Branch makeBranch(vec3 pos, mat4 transform, float scale, float time, float startTime, float endTime, vec3 seed) {

    time = clamp(  (time - startTime) / (endTime - startTime), 0., 1.);

    mat4 orientationA = transform;
    Segment A = Segment(pos, orientationA, scale * grow(time, 0., 0.3), scale * 0.1);
    
    mat4 orientationB = perturb(orientationA, seed + vec3(0.,1.,0.), 0.08);
    Segment B = Segment(endOfSegment(A), orientationB, scale * grow(time, 0.2, 0.5), scale * 0.08);
    
    mat4 orientationC = perturb(orientationB, seed + vec3(0.,2.,0.), 0.08);
    Segment C = Segment(endOfSegment(B), orientationC, scale * grow(time, 0.4, 0.7), scale * 0.06);

    mat4 orientationD = perturb(orientationC, seed + vec3(0.,3.,0.), 0.08);
    Segment D = Segment(endOfSegment(C), orientationD, scale * grow(time, 0.6, 1.0), scale * 0.04);

    return Branch(A, B, C, D);
}

QueryResult sdTree(vec3 p, vec3 pos, float scale, float time) {

    Branch trunk = makeBranch(pos, identityTransform(), 0.5 *scale, time, 0., 8., pos + vec3(0.));
    QueryResult trunkSD = sdBranch(p, trunk);

    mat4 branch1Orientation = rotate(trunk.A.orientation, X_AXIS, PI/3.);
    Branch branch1 = makeBranch(trunk.B.pos, branch1Orientation, 0.25 * scale, time, 2., 7., pos + vec3(1.,0.,0.));
    QueryResult branchSD1 = sdBranch(p, branch1);

    mat4 branch2Orientation = rotate(trunk.B.orientation, Z_AXIS, PI/3.);
    Branch branch2 = makeBranch(trunk.C.pos, branch2Orientation, 0.25 * scale, time, 4., 9., pos + vec3(2.,0.,0.));
    QueryResult branchSD2 = sdBranch(p, branch2);

    mat4 branch3Orientation = rotate(trunk.C.orientation, X_AXIS, -PI/3.);
    Branch branch3 = makeBranch(trunk.D.pos, branch3Orientation, 0.25 * scale, time, 6., 10., pos + vec3(3.,0.,0.));
    QueryResult branchSD3 = sdBranch(p, branch3);  

    return opU2( opU2(trunkSD, branchSD1), opU2(branchSD2, branchSD3));
    

    //return trunkSD;
}

QueryResult map( in vec3 p, in Params params, bool renderBox, bool renderBevel)
{
    vec3 treePos = vec3(0., 0., 2.);
    
    // plane
    QueryResult plane = sdPlane(p, params.time);
    
    QueryResult tree = sdTree( p, treePos, 1., params.time);
    
    QueryResult scene = opU2(plane, tree);

    return scene;
}


Query getQuery(in Params params)
{
    vec2 mo = iMouse.xy/iResolution.xy;
    vec2 p = (-params.iResolution.xy + 2.0*params.fragCoord)/params.iResolution.y;
    float time = params.time;
    
    // todo: move camera on right click, interact on left click: + CAMERA_MOUSE * 2. * mo.y
    //vec3 ro = vec3( 0.0, 1.0, -5.);
    vec3 ta = vec3( 0.0, 1.0, 0.0 );
    vec3 ro = ta + vec3( 4.5*cos(0.1*time + 7.0*mo.x), 1.3 + 2.0*mo.y, 4.5*sin(0.1*time + 7.0*mo.x) );

    // camera-to-world transformation
    mat3 ca = setCamera( ro, ta, 0.0 );
    // ray direction
    vec3 rd = ca * normalize( vec3(p.xy,2.0) );
    
    return Query(ro, rd);
}

// Cast a ray from origin ro in direction rd until it hits an object.
// Return (t,m,a) where t is distance traveled along the ray, and m
// is the material of the object hit, and a is an auxilliary material channel
QueryResult castRay( in Query query, in Params params, bool renderBox, bool renderBevel )
{
    float tmin = 1.0;
    float tmax = 20.0;

    vec3 rd = query.rd;
    vec3 ro = query.ro;
   
    // bounding volume
    float tp1 = (-0.1-ro.y)/rd.y; if( tp1>0.0 ) tmax = min( tmax, tp1 );
    float tp2 = (10.6-ro.y)/rd.y; if( tp2>0.0 ) { if( ro.y>10.6 ) tmin = max( tmin, tp2 );
                                                 else           tmax = min( tmax, tp2 ); }
    
    float t = tmin;


    float obj_id = -1.0;
    vec3  uvw    = vec3(0.);

    for( int i=0; i<64; i++ )
    {
	    float precis = 0.0001*t;
	    QueryResult res = map( ro+rd*t, params, renderBox, renderBevel);
        if( res.d<precis || t>tmax ) break;
        t += 0.9*res.d;
	    obj_id = res.obj_id;
        uvw = res.uvw;
    }

    if( t>tmax )
    {
        obj_id=SKY;
        uvw = vec3(0.,rd.y, 0.);
    }
    return QueryResult( t, obj_id, uvw);
}



// Cast a shadow ray from origin ro (an object surface) in direction rd
// to compute soft shadow in that direction. Returns a lower value
// (darker shadow) when there is more stuff nearby as we step along the shadow ray.
float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax, in Params params, bool renderBox, bool renderBevel)
{
	float res = 1.0;
    float t = mint;
    for( int i=0; i<16; i++ )
    {
		float h = map( ro + rd*t, params, renderBox, renderBevel).d;
        res = min( res, 6.0*h/t );
        t += clamp( h, 0.02, 0.10 );
        if( h<0.001 || t>tmax ) break;
    }
    return clamp( res, 0.0, 1.0 );
}

// Compute normal vector to surface at pos, using central differences method?
vec3 calcNormal( in vec3 pos, in Params params, bool renderBox, bool renderBevel )
{
    // epsilon = a small number
    vec2 e = vec2(1.0,-1.0)*0.5773*0.0005;
    
    return normalize( e.xyy*map( pos + e.xyy, params, renderBox, renderBevel ).d + 
					  e.yyx*map( pos + e.yyx, params, renderBox, renderBevel ).d + 
					  e.yxy*map( pos + e.yxy, params, renderBox, renderBevel ).d + 
					  e.xxx*map( pos + e.xxx, params, renderBox, renderBevel ).d );

}

// compute ambient occlusion value at given position/normal
float calcAO( in vec3 pos, in vec3 nor, in Params params, bool renderBox, bool renderBevel )
{
	float occ = 0.0;
    float sca = 1.0;
    for( int i=0; i<5; i++ )
    {
        float hr = 0.01 + 0.12*float(i)/4.0;
        vec3 aopos =  nor * hr + pos;
        float dd = map( aopos, params, renderBox, renderBevel).d;
        occ += -(dd-hr)*sca;
        sca *= 0.95;
    }
    return clamp( 1.0 - 3.0*occ, 0.0, 1.0 );    
}



// UE4's PseudoRandom function
// https://github.com/EpicGames/UnrealEngine/blob/release/Engine/Shaders/Private/Random.ush
float pseudo(vec2 v) {
    v = fract(v/128.)*128. + vec2(-64.340622, -72.465622);
    return fract(dot(v.xyx * v.xyy, vec3(20.390625, 60.703125, 2.4281209)));
}


vec3 Sky(in Params params, in vec3 uvw) {
    return clamp(SKY_BASE_COLOR + uvw.y*0.8, 0., 1.);
}

vec3 Tree(in Params params, in vec3 uvw) {
    return vec3(0.5);
}

// Interpret the material and uvw and produce info for final rendering
// todo: make this less branchy
Material mat_col(in Params params, in QueryResult queryResult)
{
    
    float x = queryResult.uvw.x;
    float y = queryResult.uvw.y;
    float obj_id = queryResult.obj_id;    
    
    vec3 nor = vec3(0.);
    float spec = 0.;
    
    // color
    vec3 sky          = Sky(params, queryResult.uvw);
    
    
    vec3 plane = 0.3 + 0.1*(mod( floor(5.0*x) + floor(5.0*y), 2.0))*vec3(1.0);
        
    vec3 tree = Tree(params, queryResult.uvw);
    
    vec3 col = 
               step(-obj_id, -1. * -1.5) * step(obj_id, -0.5)  * sky   +   // -1 -->  -1.5  < x  < -0.5
               step(-obj_id, -1. *  0.5) * step(obj_id, 1.5)   * plane +   //  1 -->   0.5  < x  <  1.5
               step(-obj_id, -1. *  1.5) * step(obj_id, 2.5)   * tree;     //  2 -->   1.5  < x  <  2.5
    
    
    return Material(col, nor, spec); 
}



// Render by fetching from the scene buffer and interpreting it to get diffuse
// TODO: Then, add in shadows, AO, etc.
vec3 render2(in vec2 fragCoord)
{

    Params params = Params(  fragCoord, iResolution.xy, mod(iTime,10.));
    Query query = getQuery(params);
    QueryResult scene = castRay( query, params, true, true );

    // Get the scene info from the scene buffer
    //vec4 scene = texelFetch(iChannel1, ivec2(fragCoord), 0);
    
    // alias some stuff from the scene buffer
    float d      = scene.d;
    float obj_id = scene.obj_id;
    vec3  uvw    = scene.uvw;
    
    // form query based on current camera position, combine with depth to get scene position
    vec3 rd = query.rd;
    vec3 ro = query.ro;
    vec3 pos = d * rd + ro;
    
    /*vec3 mouseWorldPos     = getMouseWorldPos();
    if (length(pos - mouseWorldPos) < 0.25)
    {
        return vec3(1.);
    }*/
    
    
    // material info
    Material mat = mat_col(params, scene);
    
    
    vec3 col = mat.col;

    // if not the sky, apply effects.
    if (obj_id > 0.)
    {
        vec3 nor = calcNormal( pos, params, true, true );
        vec3 ref = reflect( rd, nor ); // reflected ray

        // lighting        
        float occ = calcAO( pos, nor, params, true, true ); // ambient occlusion
		vec3  lig = normalize( SUNLIGHT_DIR ); // sunlight
		float amb = clamp( 0.5+0.5*nor.y, 0.0, 1.0 ); // ambient light
        float dif = clamp( dot( nor, lig ), 0.0, 1.0 ); // diffuse reflection from sunlight
        // backlight
        float bac = clamp( dot( nor, normalize(vec3(-lig.x,0.0,-lig.z))), 0.0, 1.0 )*clamp( 1.0-pos.y,0.0,1.0);
        float dom = smoothstep( -0.1, 0.1, ref.y ); // dome light
        float fre = pow( clamp(1.0+dot(nor,rd),0.0,1.0), 2.0 ); // fresnel
		float spe = pow(clamp( dot( ref, lig ), 0.0, 1.0 ),16.0); // specular reflection
        
        dif *= softshadow( pos, lig, 0.02, 2.5, params, true, true );
        dom *= softshadow( pos, ref, 0.02, 2.5, params, true, true );

		vec3 lin = vec3(0.0);
        lin += (1.30)*dif*vec3(1.00,0.80,0.55);
		lin += (2.00 + mat.spec)*spe*vec3(1.00,0.90,0.70)*dif;
        lin += 0.40*amb*vec3(0.40,0.60,1.00)*occ;
        lin += 0.50*dom*vec3(0.40,0.60,1.00)*occ;
        lin += 0.50*bac*vec3(0.25,0.25,0.25)*occ;
        lin += 0.25*fre*vec3(1.00,1.00,1.00)*occ;
		col = col*lin;
        
        // mix in fog?
        vec3 fog_col = SKY_BASE_COLOR;
    	col = mix( col, fog_col, 1.0-exp( -0.0002*d*d*d ) );
    }
    
    return vec3( clamp(col,0.0,1.0) );
}


void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec3 tot = vec3(0.0);
    for( int m=0; m<AA; m++ )
    for( int n=0; n<AA; n++ )
    {
        // pixel coordinates
        vec2 o = vec2(float(m),float(n)) / float(AA) - 0.5;
        //vec2 p = (2.0*(fragCoord+o)-iResolution.xy)/iResolution.y;
        vec3 col = render2(fragCoord + o);

    
    
        tot += col;

    }
    tot /= float(AA*AA);


    fragColor = vec4(tot, 1.);
}