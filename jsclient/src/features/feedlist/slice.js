import { createSlice } from "@reduxjs/toolkit";
import { storageGet, storageSet } from "../../storageUtils";

const triboolMapping = {"true": true, "false": false, "null": null};


function mergeCategoriesWithUnreads(feedListRows, unreads,
                                    isParentFolded) {
  const categories = [];
  return feedListRows.map((row) => {
    const unread = unreads[`${row.type}-${row.id}`];
    let index;
    if(row.type === "categ" || row.type === "all-categ") {
      index = categories.length * 3;
      categories.push(row.id);
    } else if (unread) {
      index = categories.indexOf(row["category_id"]) * 3 + 1 / unread;
    } else {
      index = categories.indexOf(row["category_id"]) * 3 + 2;
    }
    return { ...row, unread: unread ? unread : null, index,
             folded: typeof(row.folded) === "undefined" ? isParentFolded: row.folded };
  }).sort((row1, row2) => (row1.index - row2.index));
}

export const filterFeedRows = (rows, searchTerm) => {
    const defaultFilter = (row) => ( // will display row if
        !row.folded  // row is not folded
        || row.type === "categ" // row is a category (can't be folded)
        || row.type === "all-categ" // row is the "all categ" category (idem)
        // row is a feed without category (idem)
        || (row.type === "feed" && row["category_id"] === null)
    );
    const searchTermFilter = (row) => (
        row.type !== "categ" && row.type !== "all-categ"
        && row.str.toLowerCase().includes(searchTerm)
    );
    if (searchTerm) {
        return rows.filter(searchTermFilter);
    } else {
        return rows.filter(defaultFilter);
    }
};

const feedSlice = createSlice({
  name: "feeds",
  initialState: { loadingFeeds: false,
                  loadingUnreadCounts: false,
                  unreadToFetch: true,
                  feedListRows: [],
                  searchTerm: null,
                  unreads: {},
                  isParentFolded: storageGet("left-menu-folded", "session") === "true",
                  isOpen: triboolMapping[storageGet("left-menu-open", "session")],
                  icons: {},
                  categoryAsFeed: {},
  },
  reducers: {
    requestedFeeds: (state, action) => ({ ...state, loadingFeeds: true }),
    requestedUnreadCounts: (state, action) => ({ ...state, loadingUnreadCounts: true }),
    setSearchFilter: (state, action) => ({ ...state, searchTerm: action.payload }),
    toggleAllFolding: (state, action) => {
      const newFolding = !state.isParentFolded;
      storageSet("left-menu-folded", newFolding, "session");
      return { ...state,
               feedListRows: state.feedListRows.map((row) => {
                 return { ...row, folded: newFolding, };
               }),
               isParentFolded: newFolding };
    },
    toggleFolding: (state, action) => {
      return { ...state, feedListRows: state.feedListRows.map((row) => {
          return { ...row, folded: action.payload === row["category_id"] || (row["type"] === "categ" && row.id === action.payload) ? !row.folded : row.folded };
      })};
    },
    loadedFeeds: (state, action) => {
      const categoryAsFeed = {};
      const icons = {};
      action.payload.feedListRows.forEach((row) => {
        if(row.type === "feed" && row["icon_url"]) {
          icons[row.id] = row["icon_url"];
          categoryAsFeed[row.id] = row["category_id"];
        }
      });
      let feedListRows = action.payload.feedListRows;
      if (state.feedListRows) {  // if we already have, we're going to preserve folding
        const catAsFolding = {};
        state.feedListRows.forEach((row) => {
            if (row.type === "categ") {
                catAsFolding[row.id] = row.folded;
            }
        });
        feedListRows = feedListRows.map((row) => ({ ...row,
            folded: row.type === "categ" ? catAsFolding[row.id] : catAsFolding[row["category_id"]],
        }));
      }
      return { ...state, icons, categoryAsFeed, loadingFeeds: false,
               feedListRows: mergeCategoriesWithUnreads(feedListRows,
                                                        state.unreads,
                                                        state.isParentFolded),
      };
    },
    loadedUnreadCounts: (state, action) => ({
      ...state, loadingUnreadCounts: false, unreadToFetch: false,
      unreads: action.payload.unreads,
      feedListRows: mergeCategoriesWithUnreads(state.feedListRows,
                                               action.payload.unreads,
                                               state.isParentFolded),
    }),
    toggleMenu: (state, action) => {
      storageSet("left-menu-open", action.payload, "session");
      return { ...state, isOpen: action.payload };
    },
    changeReadCount: (state, action) => {
      const unreads = { ...state.unreads };
      let shouldFetchUnread = false;
      const readChange = action.payload.action === "unread" ? 1 : -1;
      action.payload.feedsId.forEach((feedId) => {
        const feedKey = `feed-${feedId}`;
        const catKey = `categ-${state.categoryAsFeed[feedId]}`;
        if (!unreads.hasOwnProperty(feedKey)) {
          unreads[feedKey] = 0;
        }
        if (!unreads.hasOwnProperty(catKey)) {
          unreads[catKey] = 0;
        }
        unreads[feedKey] += readChange;
        if(unreads[feedKey] < 0) {
          unreads[feedKey] = 0;
          shouldFetchUnread = true;
        }
        unreads[catKey] += readChange;
        if (unreads[catKey] < 0) {
          unreads[catKey] = 0;
          shouldFetchUnread = true;
        }
      });
      return { ...state, unreads, unreadToFetch: shouldFetchUnread,
               feedListRows: mergeCategoriesWithUnreads(state.feedListRows,
                                                        unreads,
                                                        state.isParentFolded),
      };
    },
  },
});

export const {
    changeReadCount,
    loadedFeeds,
    loadedUnreadCounts,
    requestedFeeds,
    requestedUnreadCounts,
    setSearchFilter,
    toggleAllFolding,
    toggleFolding,
    toggleMenu,
} = feedSlice.actions;
export default feedSlice.reducer;
