import { updateClusterAttrs, filterClusters } from "../features/clusterlist/slice";
import { doRetryOnTokenExpiration } from "../authSlice";
import { apiUrl, pageLength } from "../const";
import doLoadMoreClusters from "./doLoadMoreClusters";

const doEditCluster = (clusterId, payload): AppThunk => async (dispatch, getState) => {
  dispatch(updateClusterAttrs({ clusterId, ...payload }));
  if (payload["read_reason"] === null) {
    delete payload["read_reason"];
  }
  await doRetryOnTokenExpiration({
    method: "put", url: `${apiUrl}/cluster/${clusterId}`, data: payload,
  }, dispatch, getState);
  const clusterState = getState().clusters;
  if (clusterState.moreToFetch && clusterState.clusters.filter(
        filterClusters(clusterState.requestedClusterId,
                       clusterState.filters.filter)
      ).length === (pageLength / 3 * 2)) {
    dispatch(doLoadMoreClusters());
  }
};

export default doEditCluster;
