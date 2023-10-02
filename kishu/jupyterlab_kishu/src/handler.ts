import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

/**
 * Call the API extension
 *
 * @param endPoint API REST end point for the extension
 * @param init Initial values for the request
 * @returns The response body interpreted as JSON
 */
export async function requestAPI<T>(
  endPoint = '',
  init: RequestInit = {}
): Promise<T> {
  // Make request to Jupyter API
  const settings = ServerConnection.makeSettings();
  const requestUrl = URLExt.join(
    settings.baseUrl,
    'kishu', // API Namespace
    endPoint
  );

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, init, settings);
  } catch (error) {
    throw new ServerConnection.NetworkError(error as TypeError);
  }
  const data: string = await response.text();
  if (!response.ok) {
    throw new ServerConnection.ResponseError(response, data);
  }
  if (data.length > 0) {
    try {
      return JSON.parse(data);
    } catch (error) {
      console.log('Not a JSON response body.', response);
    }
  }
  throw new ServerConnection.ResponseError(response, data);
}
