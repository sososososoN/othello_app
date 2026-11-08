import { z } from "zod";

const cellSchema = z.union([z.literal(0), z.literal(1), z.literal(2)]);

const playerColorSchema = z.union([z.literal(1), z.literal(2)]);

const boardRowSchema = z.tuple([
  cellSchema,
  cellSchema,
  cellSchema,
  cellSchema,
  cellSchema,
  cellSchema,
  cellSchema,
  cellSchema,
]);

const boardSchema = z.tuple([
  boardRowSchema,
  boardRowSchema,
  boardRowSchema,
  boardRowSchema,
  boardRowSchema,
  boardRowSchema,
  boardRowSchema,
  boardRowSchema,
]);

const positionSchema = z.tuple([
  z.number().int().min(0).max(7),
  z.number().int().min(0).max(7),
]);

export const gameStateSchema = z.object({
  board: boardSchema,
  turn: cellSchema,
  message: z.string(),
  mode: z.enum(["pvp", "pvc"]),
  difficulty: z.enum(["easy", "normal", "hard"]),
  human_color: playerColorSchema,
  cpu_color: playerColorSchema.nullable(),
  valid_moves: z.array(positionSchema),
});

export const analysisResultSchema = z.object({
  best_move: positionSchema.nullable(),
  score: z.number().int().nullable(),
  depth: z.number().int().min(0),
  nodes_visited: z.number().int().min(0),
  cutoffs: z.number().int().min(0),
  elapsed_ms: z.number().min(0),
  candidates: z.array(
    z.object({
      move: positionSchema,
      minimax_score: z.number().int(),
      penalty: z.number().int(),
      total_score: z.number().int(),
    }),
  ),
  analysis_token: z.string().nullable(),
});
