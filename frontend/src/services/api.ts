import axios from "axios";
import { Item, ItemCreate } from "@/types";

const API_BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const itemsApi = {
  getAll: () => api.get<Item[]>("/api/v1/items"),
  get: (id: number) => api.get<Item>(`/api/v1/items/${id}`),
  create: (item: ItemCreate) => api.post<Item>("/api/v1/items", item),
  update: (id: number, item: Partial<ItemCreate>) =>
    api.put<Item>(`/api/v1/items/${id}`, item),
  delete: (id: number) => api.delete(`/api/v1/items/${id}`),
};

export default api;
