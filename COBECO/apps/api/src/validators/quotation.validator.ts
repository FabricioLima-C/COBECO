import { z } from 'zod';

export const quoteItemSchema = z.object({
  description: z
    .string()
    .trim()
    .min(2, 'Informe ao menos 2 caracteres para cotar')
    .max(160, 'Descrição muito longa'),
});

export const quoteListSchema = z.object({
  supplierIds: z
    .array(z.string().trim().min(1))
    .min(1, 'Selecione ao menos um fornecedor')
    .max(100)
    .optional(),
});

export const compareQuotationSchema = z
  .object({
    firstId: z.string().trim().min(1, 'Informe a primeira cotação'),
    secondId: z.string().trim().min(1, 'Informe a segunda cotação'),
  })
  .refine((value) => value.firstId !== value.secondId, {
    message: 'Selecione duas cotações diferentes',
  });

export const historyQuerySchema = z.object({
  page: z.coerce.number().int().min(1, 'Página inválida').default(1),
  pageSize: z.coerce
    .number()
    .int()
    .min(1, 'Tamanho de página inválido')
    .max(50, 'O limite é de 50 registros por página')
    .default(20),
});
