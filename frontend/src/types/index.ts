export interface Item {
  id: number;
  name: string;
  description?: string;
  price: number;
  category: string;
  created_at: string;
  updated_at: string;
}

export interface ItemCreate {
  name: string;
  description?: string;
  price: number;
  category: string;
}
