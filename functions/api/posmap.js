// Cloudflare Pages Function - 포지셔닝맵 위치 저장/로드 API
// KV 바인딩 이름: POSMAP_KV

export async function onRequestGet(context) {
  try {
    const data = await context.env.POSMAP_KV.get('positions');
    if (!data) {
      return new Response(null, { status: 404 });
    }
    return new Response(data, {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
      }
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
}

export async function onRequestPut(context) {
  try {
    const body = await context.request.text();
    JSON.parse(body); // validate JSON
    await context.env.POSMAP_KV.put('positions', body);
    return new Response(JSON.stringify({ ok: true }), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
}
