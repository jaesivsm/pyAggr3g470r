import { retrievedClustersList, requestedClustersList } from "../features/clusterlist/slice";
import { doRetryOnTokenExpiration } from "../authSlice";
import doFetchUnreadCount from "./doFetchUnreadCount";
import { apiUrl, pageLength } from "../const";

const doListClusters = (filters): AppThunk => async (dispatch, getState) => {
  dispatch(requestedClustersList({ filters }));
  const state = getState();
  const requestedFilter = state.clusters.requestedFilter;
  // counting expected result length, if different, we will reload feed count
  let expectedCount = null;
  if(!state.clusters.filters.filter) {
    let key = null;
    if(state.clusters.filters["category_id"]) {
      key = `categ-${state.clusters.filters["category_id"]}`;
    } else if (state.clusters.filters["feed_id"]) {
      key = `feed-${state.clusters.filters["feed_id"]}`;
    }
    if (key !== null && state.feeds.unreads.hasOwnProperty(key)) {
      expectedCount = state.feeds.unreads[key];
    } else if (key !== null) {
      expectedCount = 0;
    }
  }
  const result = await doRetryOnTokenExpiration({
    method: "get",
    url: `${apiUrl}/clusters?${requestedFilter}`,
  }, dispatch, getState);
  dispatch(retrievedClustersList({ requestedFilter, clusters: result.data,
                                   strat: "replace" }));
  if( // if filter allows us to compare
      // (filtering on read or liked would not work)
      expectedCount !== null
      // and that length doesn't match
      && expectedCount !== result.data.length
      // and that length isn't the max length possible for a page
      && result.data.length !== pageLength
  ) {
    dispatch(doFetchUnreadCount());
  }
};

export default doListClusters;
