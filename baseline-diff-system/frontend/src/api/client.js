import axios from 'axios';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 600000, // 10 分钟超时（扫描可能很慢）
});

export const scanRepos = async (aospPath, vendorPath) => {
  const response = await client.post('/scan_repos', {
    aosp_path: aospPath,
    vendor_path: vendorPath,
  });
  return response.data;
};

export const reanalyzeDiff = async () => {
  const response = await client.post('/reanalyze_diff');
  return response.data;
};

export const getCommits = async (filters = {}) => {
  const response = await client.get('/commits', { params: filters });
  return response.data;
};

export const setCategories = async (hash, categoryIds) => {
  const response = await client.post('/set_categories', {
    hash,
    category_ids: categoryIds,
  });
  return response.data;
};

export const getCategories = async () => {
  const response = await client.get('/categories/list');
  return response.data;
};

export const addCategory = async (name) => {
  const response = await client.post('/categories/add', { name });
  return response.data;
};

export const removeCategory = async (id) => {
  const response = await client.post('/categories/remove', { id });
  return response.data;
};

export const getStats = async () => {
  const response = await client.get('/stats');
  return response.data;
};

export const getMetadata = async () => {
  const response = await client.get('/metadata');
  return response.data;
};

export default client;
