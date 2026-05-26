import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "node:url";
import jobsRouter from "./routes/jobs.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app = express();
const PORT = process.env.PORT ?? 8000;

app.use(cors());
app.use(express.json());

app.use("/api", jobsRouter);

const clientDist = path.join(__dirname, "..", "..", "client", "dist");
app.use(express.static(clientDist));
app.get("*", (_req, res) => {
  res.sendFile(path.join(clientDist, "index.html"));
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
