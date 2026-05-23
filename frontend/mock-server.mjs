import { createServer } from "node:http";
const j = (res, data) => { res.setHeader("content-type","application/json"); res.end(JSON.stringify(data)); };
createServer((req, res) => {
  res.setHeader("access-control-allow-origin","*");
  if (req.url.startsWith("/api/scores")) return j(res, {
    overall: 73, social: 81, llmo: 65,
    social_breakdown: { critical_clusters: 1, high_clusters: 2, medium_clusters: 3 },
    llmo_breakdown: {
      citation_frequency: 60, share_of_voice: 45, citation_accuracy: 78, sentiment_quality: 70,
      per_llm: {
        claude: { score: 87, mention_rate: 95, avg_position: 1.4, drift: "low" },
        chatgpt: { score: 61, mention_rate: 80, avg_position: 2.6, drift: "high" },
        gemini: { score: 78, mention_rate: 90, avg_position: 1.8, drift: "medium" },
        perplexity: { score: 82, mention_rate: 88, avg_position: 1.5, drift: "low" },
      },
    },
    sparklines: { overall: [70,71,72,73], social: [80,81,81,81], llmo: [60,62,64,65] },
  });
  if (req.url.startsWith("/api/feed")) return j(res, { posts: [], next_cursor: null, stats: { volume_24h: 0, sentiment_7d: [], platform_distribution: {}, avg_response_minutes: 0 }});
  if (req.url.startsWith("/api/clusters")) return j(res, { clusters: [], total: 0 });
  if (req.url.startsWith("/api/queue")) return j(res, { queue: [], threshold_config: {critical:700,high:400,medium:200}, weights: {volume:10,like:2,share:5,comment:3,sentiment:3.5} });
  if (req.url.startsWith("/api/actions")) return j(res, { actions: [], total: 0 });
  if (req.url.startsWith("/api/llmo/audits")) return j(res, { audits: [] });
  return j(res, { ok: true });
}).listen(8000, () => console.log("mock on 8000"));
