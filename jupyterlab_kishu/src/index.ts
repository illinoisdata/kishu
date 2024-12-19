import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {
  ICommandPalette,
  InputDialog,
  Notification,
} from '@jupyterlab/apputils';
import {
  INotebookTracker,
} from '@jupyterlab/notebook';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ITranslator } from '@jupyterlab/translation';

import { requestAPI } from './handler';

const PLUGIN_ID = 'jupyterlab_kishu:plugin';

namespace CommandIDs {
  /**
   * Initialize Kishu on the currently viewed notebook.
   */
  export const init = 'kishu:init';

  /**
   * Checkout a commit on the currently viewed notebook.
   */
  export const checkout = 'kishu:checkout';

  /**
   * Create a commit on the currently viewed notebook.
   */
  export const commit = 'kishu:commit';

  export const undo = 'kishu:undo';
}

namespace KishuSetting {
  export let kishu_dir = "";
}

interface CommitSummary {
  commit_id: string;
  parent_id: string;
  message: string;
  timestamp: string;
  code_block?: string;
  runtime_ms?: number;
}

interface HeadBranch {
  branch_name?: string;
  commit_id?: string;
}

interface InitResult {
  status: string;
  message: string;
}

interface LogAllResult {
  commit_graph: CommitSummary[];
  head: HeadBranch;
}

interface CheckoutResult {
  status: string;
  message: string;
}

interface UndoResult {
    status: string;
    message: string;
}

interface InstrumentResult {
  status: string;
  message?: string;
}

interface CommitResult {
  status: string;
  message: string;
  reattachment: InstrumentResult;
}

function notifyWarning(message: string) {
  Notification.warning(message, { autoClose: 3000 });
}

function notifyError(message: string) {
  Notification.error(message, { autoClose: 3000 });
}

function currentNotebookPath(tracker: INotebookTracker): string | undefined {
  const widget = tracker.currentWidget;
  if (!widget) {
    console.log(`Missing tracker widget to detect currently viewed notebook.`);
    return undefined;
  }
  return widget.context.localPath;
}

function commitSummaryToString(commit: CommitSummary): string {
  const date = new Date(commit.timestamp);
  return `[${date.toLocaleString()}]: ${commit.message} (${commit.commit_id})`;
}

function extractHashFromString(inputString: string): string | undefined {
  const regex = /\(([0-9a-fA-F-]+)\)$/;
  const match = inputString.match(regex);
  if (match && match[1]) {
    return match[1];
  }
  return undefined;
}

function loadSetting(setting: ISettingRegistry.ISettings): void {
  // Read the settings and convert to the correct type
  KishuSetting.kishu_dir = setting.get('kishu_dir').composite as string;
  console.log(`Settings: kishu_dir= ${KishuSetting.kishu_dir}`);
}

function installCommands(
  app: JupyterFrontEnd,
  palette: ICommandPalette,
  translator: ITranslator,
  tracker: INotebookTracker,
) {
  const { commands } = app;
  const trans = translator.load('jupyterlab');

  /**
   * Init
   */

  commands.addCommand(CommandIDs.init, {
    label: (args) => (
      args.label && args.label == 'short'
        ? trans.__('Initialize/Re-attach')
        : trans.__('Kishu: Initialize/Re-attach...')
    ),
    execute: async (_args) => {
      // Detect currently viewed notebook.
      const notebook_path = currentNotebookPath(tracker);
      if (!notebook_path) {
        notifyError(trans.__(`No currently viewed notebook detected to initialize/attach.`));
        return;
      }

      // Make init request
      const init_promise = requestAPI<InitResult>('init', {
        method: 'POST',
        body: JSON.stringify({notebook_path: notebook_path}),
      });

      // Report.
      const notify_manager = Notification.manager;
      const notify_id = notify_manager.notify(
        trans.__(`Initializing Kishu on ${notebook_path}...`),
        'in-progress',
        { autoClose: false },
      );
      init_promise.then((init_result,) => {
        if (init_result.status != "ok") {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Kishu init failed.\n"${init_result.message}"`),
            type: 'error',
            autoClose: 3000,
          });
        } else {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Kishu init succeeded!\n"${init_result.message}"`),
            type: 'success',
            autoClose: 3000,
          });
        }
      });
    }
  });
  palette.addItem({
    command: CommandIDs.init,
    category: 'Kishu',
  });

  /**
   * Checkout
   */

  commands.addCommand(CommandIDs.checkout, {
    label: (args) => (
      args.label && args.label == 'short'
        ? trans.__('Checkout')
        : trans.__('Kishu: Checkout...')
    ),
    execute: async (_args) => {
      // Detect currently viewed notebook.
      const notebook_path = currentNotebookPath(tracker);
      if (!notebook_path) {
        notifyError(trans.__(`No currently viewed notebook detected to checkout.`));
        return;
      }

      // List all commits.
      const log_all_result = await requestAPI<LogAllResult>('log_all', {
        method: 'POST',
        body: JSON.stringify({notebook_path: notebook_path, kinds: ["manual"]}),
      });

      // Ask for the target commit ID.
      let maybe_commit_id = undefined;
      if (!log_all_result || log_all_result.commit_graph.length == 0) {
        notifyWarning(trans.__(`No Kishu commit found.`));
      } else {
        // Find the index to current commit.
        let current_idx = log_all_result.commit_graph.findIndex(
          commit => commit.commit_id === log_all_result.head.commit_id
        );
        if (current_idx == -1) {
          current_idx = log_all_result.commit_graph.length - 1;
        }

        // Show the list and ask to pick one item
        const selected_commit_str = (
          await InputDialog.getItem({
            items: log_all_result.commit_graph.map(commitSummaryToString),
            current: current_idx,
            editable: false,
            title: trans.__('Checkout to...'),
            okLabel: trans.__('Checkout')
          })
        ).value ?? undefined;
        if (selected_commit_str !== undefined) {
          maybe_commit_id = extractHashFromString(selected_commit_str);
        }
      }
      if (!maybe_commit_id) {
        return;
      }
      const commit_id: string = maybe_commit_id;

      // Make checkout request
      const checkout_promise = requestAPI<CheckoutResult>('checkout', {
        method: 'POST',
        body: JSON.stringify({notebook_path: notebook_path, commit_id: commit_id}),
      });

      // Reports.
      const notify_manager = Notification.manager;
      const notify_id = notify_manager.notify(
        trans.__(`Checking out ${commit_id}...`),
        'in-progress',
        { autoClose: false },
      );
      checkout_promise.then((checkout_result,) => {
        if (checkout_result.status != "ok") {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Kishu checkout failed.\n"${checkout_result.message}"`),
            type: 'error',
            autoClose: 3000,
          });
        } else {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Kishu checkout to ${commit_id} succeeded!`),
            type: 'success',
            autoClose: 3000,
          });
        }
      });
    }
  });
  palette.addItem({
    command: CommandIDs.checkout,
    category: 'Kishu',
  });

  /**
   * Commit
   */

  commands.addCommand(CommandIDs.commit, {
    label: (args) => (
      args.label && args.label == 'short'
        ? trans.__('Commit')
        : trans.__('Kishu: Commit...')
    ),
    execute: async (_args) => {
      // Detect currently viewed notebook.
      const notebook_path = currentNotebookPath(tracker);
      if (!notebook_path) {
        notifyError(trans.__(`No currently viewed notebook detected to commit.`));
        return;
      }

      // Ask for the commit message.
      const message = (
        await InputDialog.getText({
          placeholder: '<commit_message>',
          title: trans.__('Commit message'),
          okLabel: trans.__('Commit')
        })
      ).value ?? undefined;
      if (message == undefined) {
        return;  // Commit canceled
      }
      if (!message) {
        notifyError(trans.__(`Kishu commit requires a commit message.`));
      }

      // Make checkout request
      const commit_promise = requestAPI<CommitResult>('commit', {
        method: 'POST',
        body: JSON.stringify({notebook_path: notebook_path, message: message}),
      });

      // Reports.
      const notify_manager = Notification.manager;
      const notify_id = notify_manager.notify(
        trans.__(`Creating a commit...`),
        'in-progress',
        { autoClose: false },
      );
      commit_promise.then((commit_result,) => {
        if (commit_result.status != "ok") {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Kishu commit failed.\n"${commit_result.message}"`),
            type: 'error',
            autoClose: 3000,
          });
        } else {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Kishu commit succeeded!`),
            type: 'success',
            autoClose: 3000,
          });
        }
      });
    }
  });
  palette.addItem({
    command: CommandIDs.commit,
    category: 'Kishu',
  });

  commands.addCommand(CommandIDs.undo, {
    label: (args) => (
      args.label && args.label == 'short'
          ? trans.__('Undo Execution')
          : trans.__('Kishu: Undo Execution...')
    ),
    execute: async (_args) => {
      // Detect currently viewed notebook.
      const notebook_path = currentNotebookPath(tracker);
      if (!notebook_path) {
        notifyError(trans.__(`No currently viewed notebook detected to undo execution.`));
        return;
      }

      // Make init request
      const undo_promise = requestAPI<UndoResult>('undo', {
        method: 'POST',
        body: JSON.stringify({notebook_path: notebook_path}),
      });

      // Report.
      const notify_manager = Notification.manager;
      const notify_id = notify_manager.notify(
          trans.__(`Undoing execution for ${notebook_path}...`),
          'in-progress',
          { autoClose: false },
      );
      undo_promise.then((undo_result,) => {
        if (undo_result.status != "ok") {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Undo execution failed.\n"${undo_result.message}"`),
            type: 'error',
            autoClose: 3000,
          });
        } else {
          notify_manager.update({
            id: notify_id,
            message: trans.__(`Undo execution succeeded!`),
            type: 'success',
            autoClose: 3000,
          });
        }
      });

    }
    });
  palette.addItem({
    command: CommandIDs.undo,
    category: 'Kishu',
  });
}

/**
 * Initialization data for the jupyterlab_kishu extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  description: 'Jupyter extension to interact with Kishu',
  autoStart: true,
  requires: [ICommandPalette, ITranslator, ISettingRegistry, INotebookTracker],
  activate: (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    translator: ITranslator,
    settings: ISettingRegistry,
    tracker: INotebookTracker,
  ) => {
    Promise.all([app.restored, settings.load(PLUGIN_ID)])
      .then(([, setting]) => {
        // Setting registry.
        loadSetting(setting);
        setting.changed.connect(loadSetting);

        // Install commands.
        installCommands(app, palette, translator, tracker);
      })
      .catch(reason => {
        console.error(
          `Something went wrong when reading the settings.\n${reason}`
        );
      });
  }
};

export default plugin;
